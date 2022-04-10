package spaces

import (
	"bytes"
	"context"
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"path"
	"regexp"
	"strconv"
	"text/template"

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
}

type Instance struct {
	User       string
	Name       string
	SshPort    int
	VsCodePort int
	Status     string
}
type Manager interface {
	Create(space NewSpace) (bool, string, error)
	List(user string) ([]Instance, error)
	Stop(user, name string) error
	Kill(user, name string) error
}

func New(dir string) Manager {
	return &dockerComposeManager{
		root: dir,
	}
}

type dockerComposeManager struct {
	root string
	cli  *client.Client
}

func (dcm *dockerComposeManager) client() (*client.Client, error) {
	if dcm.cli == nil {
		cli, err := client.NewClientWithOpts(client.FromEnv)

		if err != nil {
			fmt.Fprintf(os.Stderr, "Error getting docker client: %v", err)
			return nil, err
		}
		dcm.cli = cli
	}
	return dcm.cli, nil
}

func (dcm *dockerComposeManager) rootDir() string {
	if dcm.root != "" {
		return dcm.root
	}
	pwd, err := os.Getwd()
	if err != nil {
		panic(err)
	}
	return pwd
}

func (dcm *dockerComposeManager) Create(space NewSpace) (bool, string, error) {

	key := fmt.Sprintf("%s/%s", space.User, space.Name)

	dir := path.Join(dcm.rootDir(), key)

	// todo check if running
	if stat, err := os.Stat(dir); err == nil && stat.IsDir() {
		return true, "", nil
	}

	err := createSpaceFiles(dir, space)
	output := &bytes.Buffer{}

	// start docker compose!
	cmd := exec.Command("docker", "compose", "up", "-d")
	cmd.Dir = dir
	cmd.Stdout = output
	cmd.Stderr = output

	err = cmd.Run()

	// cli, err := client.NewClientWithOpts(client.FromEnv)

	// if err != nil {
	// 	return false, err
	// }
	return err == nil, output.String(), err
}

func (dcm *dockerComposeManager) List(user string) ([]Instance, error) {

	dir := path.Join(dcm.rootDir(), user)

	files, err := ioutil.ReadDir(dir)

	instances := []Instance{}
	if err != nil {
		return nil, err
	}

	for _, f := range files {
		if !f.IsDir() {
			continue
		}

		i := Instance{
			User: user,
			Name: f.Name(),
		}

		// make sure there is a dc file in there
		stat, err := os.Stat(path.Join(dir, f.Name(), "docker-compose.yaml"))

		if err != nil || stat.IsDir() {
			continue
		}

		// check status
		cli, err := dcm.client()
		if err != nil {
			return nil, err
		}

		key := fmt.Sprintf("space-%s-%s", i.User, i.Name)
		j, err := cli.ContainerInspect(context.Background(), key)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Error inspecting %q: %v", key, err)
		}

		i.Status = j.State.Status

		i.SshPort = getPort(22, j.NetworkSettings.Ports)
		i.VsCodePort = getPort(8080, j.NetworkSettings.Ports)

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
	panic("not implemented") // TODO: Implement
}

var spaceNames = []string{
	"grover",
	"cookie",
	"count",
	"bert",
	"ernie",
	"bigbird",
	"elmo",
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

	if space.Image == "" {
		space.Image = "docker-env-base:local"
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
	// write it
	return ioutil.WriteFile(path.Join(dir, "docker-compose.yml"), []byte(b), os.ModePerm)

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
        container_name: dind-{{.User}}-{{.Name}}
        privileged: true
        expose:
            - 2375
            - 2376
        environment:
            - DOCKER_TLS_CERTDIR=
        volumes:
            - "./image-cache:/var/lib/docker/overlay2"

    {{.User}}-{{.Name}}-space:
        image: {{.Image}}
        container_name: space-{{.User}}-{{.Name}}
        ports:
            - "{{.SshPort}}:22"
            - "{{.VsCodePort}}:8080"
        environment:
            DOCKER_HOST: tcp://dind:2375
            ENV_USER: {{.User}}
            ENV_USER_PASSWORD: {{.Password}}
        volumes:
            - "{{.User}}-{{.Name}}-volume:/home/{{.User}}"
            {{ if .PubKey }}- "pubkey:/tmp/pubkey"{{ end }}
volumes:
  {{.User}}-{{.Name}}-volume:

`
