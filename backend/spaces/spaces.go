package spaces

import (
	"bytes"
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"path"
	"text/template"

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

func Start(space NewSpace) (bool, string, error) {

	// check if we already have one of this name
	key := fmt.Sprintf("%s/%s", space.User, space.Name)

	// todo check if running
	if stat, err := os.Stat(key); err == nil && stat.IsDir() {
		return true, "", nil
	}

	pwd, err := os.Getwd()
	if err != nil {
		return false, "", err
	}

	dir := path.Join(pwd, key)
	err = createSpaceFiles(dir, space)
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
