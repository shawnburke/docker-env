package spaces

import (
	"fmt"
	"net"
	"os"
	"path"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/require"
	"gopkg.in/yaml.v3"
)

func TestWriteFiles(t *testing.T) {
	// pwd, err := os.Getwd()
	// require.NoError(t, err)
	dir := path.Join(os.TempDir(), ".tmp", "docker-env")
	err := os.MkdirAll(dir, os.ModeDir|os.ModePerm)
	require.NoError(t, err)

	s := NewSpace{
		User:        "the-user",
		Password:    "the-password",
		Name:        "the-space",
		DnsSearch:   "search.com",
		Nameservers: []string{"1.2.3.4", "8.8.8.8"},
	}

	err = createSpaceFiles(dir, s)
	require.NoError(t, err)

	stat, err := os.Stat(path.Join(dir, dockerComposeYml))
	require.NoError(t, err)
	require.True(t, stat.Size() > 0)

}

func TestCreateYaml(t *testing.T) {
	s := NewSpace{
		User:        "the-user",
		Password:    "the-password",
		Name:        "the-space",
		DnsSearch:   "search.com",
		Nameservers: []string{"1.2.3.4", "8.8.8.8"},
	}

	dc, err := createDockerCompose(s)
	require.NoError(t, err)

	parsed := map[string]interface{}{}
	err = yaml.Unmarshal([]byte(dc), parsed)
	require.NoError(t, err)

	raw, err := yaml.Marshal(parsed)
	require.NoError(t, err)

	y := strings.Trim(string(raw), " \n")
	fmt.Println(y)

	expected := `services:
    docker:
        command: --dns 1.2.3.4 --dns 8.8.8.8 --dns-search search.com
        container_name: dind-the-user-the-space
        environment:
            - DOCKER_TLS_CERTDIR=
        expose:
            - 2375
            - 2376
        image: docker:dind
        privileged: true
        restart: unless-stopped
    workspace:
        container_name: space-the-user-the-space
        environment:
            DOCKER_HOST: tcp://docker:2375
            ENV_USER: the-user
            ENV_USER_PASSWORD: the-password
        hostname: the-user-the-space
        image: null
        ports:
            - "0:22"
            - 0:8080
            - 0:9999
        restart: unless-stopped
        volumes:
            - the-user-the-space-volume:/home/the-user
version: "3"
volumes:
    the-user-the-space-volume: null`
	require.Equal(t, expected, y)

}

func TestNameserverArgs(t *testing.T) {
	s := NewSpace{
		User:        "the-user",
		Password:    "the-password",
		Name:        "the-space",
		Nameservers: strings.Split("", ","),
	}

	require.Equal(t, "", s.DockerArgs())

}

func TestNameserverArgsStripQuotes(t *testing.T) {
	s := NewSpace{
		User:        "the-user",
		Password:    "the-password",
		Name:        "the-space",
		Nameservers: strings.Split(`"1.2.3.4,8.8.4.1"`, ","),
	}

	require.Equal(t, "--dns 1.2.3.4 --dns 8.8.4.1", s.DockerArgs())

}

func TestCreateYamlNoDns(t *testing.T) {

	s := NewSpace{
		User:     "the-user",
		Password: "the-password",
		Name:     "the-space",
	}

	dc, err := createDockerCompose(s)
	require.NoError(t, err)
	err = yaml.Unmarshal([]byte(dc), map[string]interface{}{})
	require.NoError(t, err)

	require.NotContains(t, dc, "--dns", dc)

}

func TestCheckOpenPort(t *testing.T) {
	l, err := net.Listen("tcp", "0.0.0.0:0")
	require.NoError(t, err)

	done := make(chan bool)
	require.NotNil(t, l)

	addr := l.Addr().String()
	lastIndex := strings.LastIndex(addr, ":")
	port, _ := strconv.Atoi(addr[lastIndex+1:])

	open := check_open("test", "0.0.0.0", port)
	time.Sleep(time.Millisecond * 50)

	require.True(t, open)
	close(done)
	l.Close()

}

func TestParseOpenPorts(t *testing.T) {
	payload := `8080=label|msg
	3000=My webserver
	`

	dcm := &dockerComposeManager{}
	ports := dcm.getOpenPorts(payload)

	require.Len(t, ports, 2)
	require.Equal(t, 8080, ports[0].RemotePort)
	require.Equal(t, "msg", ports[0].Message)
}
