package spaces

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"os"
	"os/exec"
	"path"
	"regexp"
	"strconv"
	"text/template"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
	"github.com/phayes/freeport"
)

type NewSpace struct {
	User       string
	Name       string
	Password   string
	Image      string
	PubKey     string
	SshPort    int
	VsCodePort int
	Root       string
	UserRoot   string
}

func (ns NewSpace) PubKeyEncoded() string {
	if ns.PubKey == "" {
		return ""
	}

	return base64.URLEncoding.EncodeToString([]byte(ns.PubKey))

}

type Instance struct {
	User           string          `json:"user"`
	Name           string          `json:"name"`
	SshPort        int             `json:"ssh_port"`
	Ports          []instancePort  `json:"ports"`
	Status         string          `json:"status"`
	ContainerStats *ContainerStats `json:"container_stats,omitempty"`
}

type instancePort struct {
	Label   string `json:"label"`
	Message string `json:"message"`
	Port    int    `json:"port"`
}
type Manager interface {
	Create(space NewSpace) (*Instance, string, error)
	List(user string) ([]Instance, error)
	Get(user, name string, stats bool) (Instance, error)
	Stop(user, name string) error
	Kill(user, name string) error
}

const DefaultImageName = "docker-env-base:local"
const dockerComposeYml = "docker-compose.yml"

var spaceNames = []string{
	"grover",
	"elmo",
	"bert",
	"ernie",
	"cookie",
	"bigbird",
	"count",
}

func New(dir string) Manager {

	defaultImage := DefaultImageName

	if env := os.Getenv("DEFAULT_IMAGE"); env != "" {
		defaultImage = env
	}

	return &dockerComposeManager{
		root:         dir,
		uroot:        path.Join(dir, "spaces"),
		defaultImage: defaultImage,
	}
}

type dockerComposeManager struct {
	root         string
	uroot        string
	cli          *client.Client
	defaultImage string
}

func (dcm *dockerComposeManager) client() (*client.Client, error) {
	if dcm.cli == nil {
		cli, err := client.NewClientWithOpts(client.FromEnv)

		if err != nil {
			fmt.Fprintf(os.Stderr, "Error getting docker client: %v", err)
			return nil, err
		}
		cli.NegotiateAPIVersion(context.Background())
		dcm.cli = cli
	}
	return dcm.cli, nil
}

func (dcm *dockerComposeManager) userRoot() string {
	if dcm.uroot == "" {
		panic("no root set")
	}
	return dcm.uroot
}

func (dcm *dockerComposeManager) pickName(user string) string {

	for _, n := range spaceNames {

		p := path.Join(dcm.userRoot(), user, n, dockerComposeYml)

		if _, err := os.Stat(p); os.IsNotExist(err) {
			return n
		}
	}
	return ""
}

func (dcm *dockerComposeManager) Create(space NewSpace) (*Instance, string, error) {

	if space.Name == "" {
		space.Name = dcm.pickName(space.User)
	}

	if space.Name == "" {
		return nil, "Failed to pick name", fmt.Errorf("No name was provided, all default names are in use.")
	}

	key := fmt.Sprintf("%s/%s", space.User, space.Name)

	dir := path.Join(dcm.userRoot(), key)

	// todo check if running
	if stat, err := os.Stat(dir); err == nil && stat.IsDir() {

		instance, err := dcm.Get(space.User, space.Name, false)

		if err == nil && instance.Name == space.Name {
			return &instance, "", os.ErrExist
		}
	}

	space.UserRoot = dcm.userRoot()
	space.Root = dcm.root
	log.Printf("Creating space %s for user %s at %s\n:%+v", space.Name, space.User, space.UserRoot, space)

	if space.Image == "" {
		space.Image = dcm.defaultImage
	}

	// make sure the image exists
	cli, err := dcm.client()
	if err != nil {
		return nil, err.Error(), fmt.Errorf("Error getting client: %v", err)
	}

	_, _, err = cli.ImageInspectWithRaw(context.Background(), space.Image)

	if err != nil {
		return nil, "Can not find image " + space.Image, err
	}

	err = createSpaceFiles(dir, space)
	if err != nil {
		return nil, err.Error(), err
	}
	output := &bytes.Buffer{}

	log.Printf("Starting space")
	cmd := exec.Command("docker-compose", "up", "-d")
	cmd.Dir = dir
	cmd.Stdout = output
	cmd.Stderr = output

	err = cmd.Run()

	if err != nil {
		log.Printf("Failed to start: %v\n%v", err, output)
		return nil, output.String(), err
	}

	log.Printf("Successfully started %s", key)

	i, err := dcm.Get(space.User, space.Name, false)

	if err != nil {
		return nil, err.Error(), err
	}

	return &i, output.String(), nil
}

type ContainerStats struct {
	MemoryStats types.MemoryStats `json:"memory_stats"`
	CpuStats    types.CPUStats    `json:"cpu_stats"`
}

func (dcm *dockerComposeManager) stats(user, name string) (*ContainerStats, error) {

	key := fmt.Sprintf("space-%s-%s", user, name)

	cli, err := dcm.client()
	if err != nil {
		return nil, err
	}
	s, err := cli.ContainerStats(context.Background(), key, false)
	if err != nil {
		return nil, err
	}

	defer s.Body.Close()
	body, err := ioutil.ReadAll(s.Body)
	if err != nil {
		return nil, err
	}

	cs := ContainerStats{}
	err = json.Unmarshal(body, &cs)
	return &cs, err
}

func (dcm *dockerComposeManager) Get(user, name string, stats bool) (Instance, error) {

	i := &Instance{
		User: user,
		Name: name,
	}

	// make sure there is a dc file in there
	stat, err := os.Stat(path.Join(dcm.userRoot(), user, name, dockerComposeYml))

	if err != nil || stat.IsDir() {
		return Instance{}, os.ErrNotExist
	}

	// check status
	cli, err := dcm.client()
	if err != nil {
		return Instance{}, err
	}

	key := fmt.Sprintf("space-%s-%s", i.User, i.Name)
	j, err := cli.ContainerInspect(context.Background(), key)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error inspecting %q: %v", key, err)
		return Instance{}, err
	}

	i.Status = j.State.Status

	i.SshPort = getPort(22, j.NetworkSettings.Ports)
	i.Ports = append(i.Ports, instancePort{
		Port:    getPort(8080, j.NetworkSettings.Ports),
		Label:   "VSCode Browser",
		Message: "Connect to VSCode browser at http://localhost:LOCAL_PORT",
	})

	if stats {
		s, err := dcm.stats(user, name)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error getting stats: %v", err)
		} else {
			i.ContainerStats = s
		}
	}

	return *i, nil
}

func (dcm *dockerComposeManager) List(user string) ([]Instance, error) {

	dir := path.Join(dcm.userRoot(), user)
	instances := []Instance{}

	files, err := ioutil.ReadDir(dir)

	if os.IsNotExist(err) {
		return instances, nil
	}

	if err != nil {
		return instances, err
	}

	for _, f := range files {
		if !f.IsDir() {
			continue
		}

		i, err := dcm.Get(user, f.Name(), false)

		if os.IsNotExist(err) {
			continue
		}

		if err != nil {
			fmt.Fprintf(os.Stderr, "Error getting instance %s.%s: %v", user, f.Name(), err)
			continue
		}

		instances = append(instances, i)
	}

	return instances, nil

}

var regexPortParse = regexp.MustCompile(`(\d+)(/tcp)?`)

func getPort(port int, pm nat.PortMap) int {
	if pb, ok := pm[nat.Port(fmt.Sprintf("%d/tcp", port))]; ok {
		for _, p := range pb {
			match := regexPortParse.FindStringSubmatch(p.HostPort)
			if match != nil {
				port, err := strconv.Atoi(match[1])
				if err == nil {
					return port
				}
			}
		}
	}
	return 0
}

func (dcm *dockerComposeManager) Stop(user string, name string) error {
	panic("not implemented") // TODO: Implement
}

func (dcm *dockerComposeManager) Kill(user string, name string) error {
	i, err := dcm.Get(user, name, false)

	if err != nil {
		return err
	}

	dir := path.Join(dcm.userRoot(), i.User, i.Name)

	output := &bytes.Buffer{}

	cmd := exec.Command("docker-compose", "down")
	cmd.Dir = dir
	cmd.Stdout = output
	cmd.Stderr = output
	err = cmd.Run()

	if err != nil {
		return err
	}

	return os.RemoveAll(dir)

}

func createSpaceFiles(dir string, space NewSpace) error {

	if space.SshPort == 0 {
		port, err := freeport.GetFreePort()
		if err != nil {
			return err
		}
		space.SshPort = port
	}

	if space.VsCodePort == 0 {
		port, err := freeport.GetFreePort()
		if err != nil {
			return err
		}
		space.VsCodePort = port
	}

	// create the dir
	err := os.MkdirAll(dir, os.ModeDir|os.ModePerm)
	if err != nil {
		return err
	}

	b, err := createDockerCompose(space)
	if err != nil {
		return err
	}

	if space.PubKey != "" {
		err = ioutil.WriteFile(path.Join(dir, "pubkey"), []byte(space.PubKey), os.ModePerm)
		if err != nil {
			return err
		}
	}

	// write it
	return ioutil.WriteFile(path.Join(dir, dockerComposeYml), []byte(b), os.ModePerm)

}

func createDockerCompose(space NewSpace) (string, error) {
	// template the docker env file

	t := template.New("docker-compose")
	templ, err := t.Parse(dockerComposeTemplate)

	buf := &bytes.Buffer{}
	err = templ.Execute(buf, &space)

	if err != nil {
		return "", err
	}

	return string(buf.Bytes()), nil

}

const dockerComposeTemplate = `
version: "3"

services:

    {{.User}}-{{.Name}}-dind:
        image: docker:dind
        restart: unless-stopped
        container_name: "dind-{{.User}}-{{.Name}}"
        privileged: true
        expose:
            - 2375
            - 2376
        environment:
            - DOCKER_TLS_CERTDIR=
        volumes:
            - "{{.Root}}/image-cache:/var/lib/docker/overlay2"

    {{.User}}-{{.Name}}-space:
        image: {{.Image}}
        restart: unless-stopped
        hostname: "{{.User}}-{{.Name}}"
        container_name: "space-{{.User}}-{{.Name}}"
        ports:
            - "{{.SshPort}}:22"
            - "{{.VsCodePort}}:8080"
        environment:
            DOCKER_HOST: "tcp://{{.User}}-{{.Name}}-dind:2375"
            ENV_USER: "{{.User}}"
            ENV_USER_PASSWORD: "{{.Password}}"
            {{ if .PubKey }}PUBKEY: "{{.PubKeyEncoded}}"{{ end }}
        volumes:
            - "{{.User}}-{{.Name}}-volume:/home/{{.User}}"
volumes:
  {{.User}}-{{.Name}}-volume:

`
