package spaces

import (
	"bytes"
	"context"
	_ "embed"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net"
	"os"
	"os/exec"
	"path"
	"regexp"
	"strconv"
	"strings"
	"text/template"
	"time"

	"github.com/docker/docker/api/types"
	"github.com/docker/docker/client"
	"github.com/docker/go-connections/nat"
	"github.com/phayes/freeport"
)

type NewSpace struct {
	User          string
	Name          string
	Password      string
	Image         string
	PubKey        string
	SshPort       int
	VsCodePort    int
	ProjectorPort int
	Root          string
	UserRoot      string

	params Params
}

func (ns NewSpace) DockerArgs() string {

	args := []string{
		"--tls=false",
	}

	for _, ns := range ns.params.DnsNameservers {
		ns := strings.Trim(ns, " \t'\"")
		if ns != "" {
			args = append(args, "--dns "+ns)
		}
	}

	if len(ns.params.DnsSearch) > 0 {
		args = append(args, "--dns-search "+strings.Trim(ns.params.DnsSearch, "\t '\""))
	}

	return strings.Join(args, " ")
}

func (ns NewSpace) Params() Params {
	return ns.params
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
	Host           string          `json:"host,omitempty"`
	SshPort        int             `json:"ssh_port"`
	Ports          []instancePort  `json:"ports,omitempty"`
	Status         string          `json:"status"`
	ContainerStats *ContainerStats `json:"container_stats,omitempty"`
}

type instancePort struct {
	Label      string `json:"label"`
	Message    string `json:"message"`
	Port       int    `json:"port"`
	RemotePort int    `json:"remote_port"`
}
type Manager interface {
	Create(space NewSpace) (*Instance, string, error)
	List(user string) ([]Instance, error)
	Get(user, name string, stats bool) (Instance, error)
	Start(user, name string) error
	Stop(user, name string) error
	Kill(user, name string) error
	Restart(user, name string) error
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

type Params struct {
	DefaultImage   string
	DnsNameservers []string
	DnsSearch      string
	CopyHostDns    bool
	Dir            string
}

func (p Params) Sanitize() Params {
	cutset := "\"' \t"
	p.Dir = strings.Trim(p.Dir, cutset)

	p.DefaultImage = strings.Trim(p.DefaultImage, cutset)
	p.DnsSearch = strings.Trim(p.DnsSearch, cutset)
	for i := len(p.DnsNameservers) - 1; i >= 0; i-- {
		p.DnsNameservers[i] = strings.Trim(p.DnsNameservers[i], cutset)
		if p.DnsNameservers[i] == "" {
			p.DnsNameservers = p.DnsNameservers[0:i]
		}
	}
	return p
}

func New(p Params) Manager {

	p = p.Sanitize()

	defaultImage := DefaultImageName

	if p.DefaultImage == "" {
		p.DefaultImage = DefaultImageName
	}

	dcm := &dockerComposeManager{
		root:         p.Dir,
		uroot:        path.Join(p.Dir, "spaces"),
		defaultImage: defaultImage,
		params:       p,
	}

	if len(p.DnsNameservers) > 0 {
		log.Printf("Using custom nameservers: %s", strings.Join(p.DnsNameservers, ","))
	}

	if p.DnsSearch != "" {
		log.Printf("Using custom DNS search domain: %s", p.DnsSearch)
	}

	return dcm
}

type dockerComposeManager struct {
	root         string
	uroot        string
	cli          *client.Client
	defaultImage string
	params       Params
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

func (dcm *dockerComposeManager) dockerCompose(dir string, args ...string) (string, error) {
	output := &bytes.Buffer{}

	cmd := exec.Command("docker-compose", args...)
	cmd.Dir = dir
	cmd.Stdout = output
	cmd.Stderr = output

	err := cmd.Run()

	return output.String(), err
}

func (dcm *dockerComposeManager) Create(space NewSpace) (*Instance, string, error) {

	if space.Name == "" {
		space.Name = dcm.pickName(space.User)
	}

	if space.Name == "" {
		return nil, "Failed to pick name", fmt.Errorf("No name was provided, all default names are in use.")
	}

	key := fmt.Sprintf("%s/%s", space.User, space.Name)

	dir, exists := dcm.getDCDir(space.User, space.Name)

	if exists {
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

	space.params = dcm.params

	err = createSpaceFiles(dir, space)
	if err != nil {
		return nil, err.Error(), err
	}

	log.Printf("Starting space")

	output, err := dcm.dockerCompose(dir, "up", "-d")

	if err != nil {
		log.Printf("Error: %v\noutput:\n%v\n", err.Error(), output)
		return nil, output, err
	}

	log.Printf("Successfully started %s", key)

	i, err := dcm.Get(space.User, space.Name, false)

	if err != nil {
		return nil, err.Error(), err
	}

	return &i, output, nil
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

func check_open(label, host string, port int) bool {
	timeout := time.Millisecond * 100
	hostport := net.JoinHostPort(host, fmt.Sprintf("%d", port))
	open := false

	defer func() {
		log.Printf("hostport %s for %s open: %v", hostport, label, open)
	}()
	conn, err := net.DialTimeout("tcp", hostport, timeout)
	if err != nil || conn == nil {
		return false
	}
	open = true
	defer conn.Close()
	return true
}

func (dcm *dockerComposeManager) getOpenPorts(payload string) []instancePort {

	exp := regexp.MustCompile(`(?m)(\d+)=(.*?)(\|(.*))?$`)

	iPorts := []instancePort{}
	matches := exp.FindAllStringSubmatch(payload, -1)
	for _, match := range matches {

		port, err := strconv.Atoi(match[1])
		if err != nil {
			log.Printf("Couldn't parse port: %q", match[1])
			continue
		}

		iPorts = append(iPorts, instancePort{
			RemotePort: port,
			Label:      match[2],
			Message:    match[4],
		})
	}

	return iPorts
}

func (dcm *dockerComposeManager) checkDCFile(user, name string) bool {
	// make sure there is a dc file in there
	dcDir, _ := dcm.getDCDir(user, name)
	stat, err := os.Stat(path.Join(dcDir, dockerComposeYml))
	return err == nil && !stat.IsDir()
}

func (dcm *dockerComposeManager) getDCDir(user, name string) (string, bool) {
	dir := path.Join(dcm.userRoot(), user, name)

	exists := false
	if s, err := os.Stat(dir); err == nil && s != nil && s.IsDir() {
		exists = true
	}
	return dir, exists
}

func (dcm *dockerComposeManager) Get(user, name string, stats bool) (Instance, error) {

	i := &Instance{
		User: user,
		Name: name,
	}

	if !dcm.checkDCFile(user, name) {
		return Instance{}, os.ErrNotExist
	}

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
	if j.State.Status != "running" {
		return *i, nil
	}

	i.SshPort = getPort(22, j.NetworkSettings.Ports)

	// check open ports

	output := &bytes.Buffer{}

	cmd := exec.Command("docker", "exec", key, "open-ports")
	cmd.Stdout = output
	cmd.Stderr = output
	err = cmd.Run()

	if err != nil {

		if strings.Contains(output.String(), "executable file not found") {
			log.Println("Error: can't get ports (open-ports not installed)")
			return *i, nil
		}

		return Instance{}, fmt.Errorf("error running docker exec: %v", output.String())
	}

	i.Ports = dcm.getOpenPorts(output.String())

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
	dir, exists := dcm.getDCDir(user, name)
	if !exists {
		return os.ErrNotExist
	}

	i, err := dcm.Get(user, name, false)

	if err != nil {
		return err
	}

	switch i.Status {
	case "running":
		break
	case "stopped", "exited":
		return nil
	default:
		return os.ErrInvalid
	}

	output, err := dcm.dockerCompose(dir, "stop")

	if err != nil {
		fmt.Println("Failed to up:\n", output)
		return err
	}

	return nil
}

func (dcm *dockerComposeManager) Start(user string, name string) error {
	dir, exists := dcm.getDCDir(user, name)
	if !exists {
		return os.ErrNotExist
	}

	i, err := dcm.Get(user, name, false)

	if err != nil {
		return err
	}

	switch i.Status {
	case "running":
		return nil
	case "stopped", "exited":
		break
	default:
		return os.ErrInvalid
	}

	output, err := dcm.dockerCompose(dir, "up", "-d")

	if err != nil {
		fmt.Println("Failed to up:\n", output)
		return err
	}

	return nil

}

func (dcm *dockerComposeManager) Restart(user string, name string) error {

	i, err := dcm.Get(user, name, false)

	if err != nil {
		return err
	}

	if i.Status != "running" {
		return fmt.Errorf("instance %q is not running, so cannot restart", name)
	}

	dir, _ := dcm.getDCDir(user, name)

	output, err := dcm.dockerCompose(dir, "down")

	if err != nil {
		return fmt.Errorf("Failed to stop running instance: %v, output=\n%s\n", err, output)
	}

	output, err = dcm.dockerCompose(dir, "up", "-d")

	if err != nil {
		return fmt.Errorf("Failed to restart stopped instance: %v, output=\n%s\n", err, output)
	}

	return nil

}

func (dcm *dockerComposeManager) Kill(user string, name string) error {
	i, err := dcm.Get(user, name, false)

	if err != nil {
		return err
	}

	dir, _ := dcm.getDCDir(i.User, i.Name)

	output, err := dcm.dockerCompose(dir, "down")

	if err != nil {
		fmt.Println("Failed to destroy")
		fmt.Println(output)
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

	port, err := freeport.GetFreePort()
	if err != nil {
		return err
	}
	space.ProjectorPort = port

	// create the dir
	err = os.MkdirAll(dir, os.ModeDir|os.ModePerm)
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

	return buf.String(), nil

}

//go:embed docker-compose-template.yml
var dockerComposeTemplate string
