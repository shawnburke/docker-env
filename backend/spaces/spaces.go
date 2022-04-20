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

	Nameservers      []string
	DnsSearch        string
	ImageCacheVolume string
}

func (ns NewSpace) DockerArgs() string {

	args := []string{}
	if len(ns.Nameservers) > 0 {
		for _, ns := range ns.Nameservers {
			ns := strings.Trim(ns, " \t'\"")
			if ns != "" {
				args = append(args, "--dns "+ns)
			}
		}
	}

	if len(ns.DnsSearch) > 0 {
		args = append(args, "--dns-search "+strings.Trim(ns.DnsSearch, "\t '\""))
	}

	return strings.Join(args, " ")
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

type Params struct {
	DefaultImage   string
	DnsNameservers []string
	DnsSearch      string
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
		root:           p.Dir,
		uroot:          path.Join(p.Dir, "spaces"),
		defaultImage:   defaultImage,
		dnsNameservers: p.DnsNameservers,
		dnsSearch:      p.DnsSearch,
	}

	if len(dcm.dnsNameservers) > 0 {
		log.Printf("Using custom nameservers: %s", strings.Join(p.DnsNameservers, ","))
	}

	if dcm.dnsSearch != "" {
		log.Printf("Using custom DNS search domain: %s", p.DnsSearch)
	}

	return dcm
}

type dockerComposeManager struct {
	root           string
	uroot          string
	cli            *client.Client
	defaultImage   string
	dnsNameservers []string
	dnsSearch      string
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

	// space.ImageCacheVolume = imageCacheVolumeName
	// err = dcm.ensureImageCache(imageCacheVolumeName)
	// if err != nil {
	// 	return nil, err.Error(), err
	// }

	space.Nameservers = dcm.dnsNameservers
	space.DnsSearch = dcm.dnsSearch

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

// const imageCacheVolumeName = "image-cache-volume"

// func (dcm *dockerComposeManager) ensureImageCache(name string) error {

// 	cli, err := dcm.client()
// 	if err != nil {
// 		return err
// 	}

// 	tryCreate := func(name string) error {
// 		_, err = cli.VolumeInspect(context.Background(), name)

// 		if err != nil {

// 			log.Printf("Creating shared image cache: %s`", name)
// 			_, err = cli.VolumeCreate(context.Background(), volume.VolumeCreateBody{
// 				Name:   name,
// 				Driver: "local",
// 			})

// 			if err != nil {
// 				return fmt.Errorf("Failed to create  cache volume %q: %v", name, err)
// 			}
// 		}
// 		return err
// 	}

// 	for _, n := range []string{name} {
// 		err = tryCreate(n)
// 		if err != nil {
// 			return err
// 		}
// 	}

// 	return nil

// }

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

func (dcm *dockerComposeManager) getOpenPorts(ns *types.NetworkSettings) []instancePort {

	iPorts := []instancePort{}

	if ns == nil {
		return iPorts
	}

	gateway := ""
	for _, n := range ns.Networks {
		gateway = n.Gateway
		break
	}

	ports := []instancePort{
		{
			RemotePort: 8080,
			Label:      "VSCode Browser",
			Message:    "Connect to VSCode browser at http://localhost:LOCAL_PORT",
		},
		{
			RemotePort: 9999,
			Label:      "IntelliJ Projector",
			Message:    "Connect to IntelliJ browser at http://localhost:LOCAL_PORT",
		},
	}

	// walk for open ports
	for _, ip := range ports {
		exPort := getPort(ip.RemotePort, ns.Ports)
		if check_open(ip.Label, "localhost", exPort) || check_open(ip.Label, gateway, exPort) {
			ip.Port = exPort
			iPorts = append(iPorts, ip)
		}
	}
	return iPorts
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

	i.SshPort = getPort(22, j.NetworkSettings.Ports)
	i.Status = j.State.Status

	i.Ports = dcm.getOpenPorts(j.NetworkSettings)

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
