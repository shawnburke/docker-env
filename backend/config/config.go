package config

import (
	"io/ioutil"
	"os"
	"path"
	"strconv"
	"strings"

	"gopkg.in/yaml.v3"
)

const DefaultImageName = "docker-env-base:local"

type Config struct {
	Port            int      `yaml:"port,omitempty"`
	DefaultImage    string   `yaml:"default_image,omitempty"`
	DnsNameservers  []string `yaml:"dns_nameservers,omitempty"`
	DnsSearch       string   `yaml:"dns_search,omitempty"`
	DnsCopyFromHost bool     `yaml:"dns_copy_from_host,omitempty"`
	Dir             string   `yaml:"dir,omitempty"`
}

func Load(configDir string) Config {

	if configDir == "" {
		d, err := os.Getwd()
		if err != nil {
			panic(err)
		}
		configDir = d
	}

	userdir, err := os.UserHomeDir()
	if err != nil {
		userdir = configDir
	}

	c := Config{
		Port:         3001,
		Dir:          path.Join(userdir, ".docker-env"),
		DefaultImage: DefaultImageName,
	}

	defer func() {
		// override with any env vars

		if env := os.Getenv("PORT"); env != "" {
			p, err := strconv.ParseInt(env, 10, 32)
			if err != nil {
				panic(err)
			}
			c.Port = int(p)
		}

		if d := os.Getenv("DIR"); d != "" {
			c.Dir = d
		}

		if d := os.Getenv("DEFAULT_IMAGE"); d != "" {
			c.DefaultImage = d
		}

		if d := os.Getenv("DNS_SEARCH"); d != "" {
			c.DnsSearch = d
		}

		if os.Getenv("COPY_HOST_DNS") == "true" || os.Getenv("COPY_HOST_DNS") == "1" {
			c.DnsCopyFromHost = true
		}

		if d := os.Getenv("DNS_NAMESERVERS"); d != "" {
			c.DnsNameservers = strings.Split(d, ",")
		}
	}()

	raw, err := ioutil.ReadFile(path.Join(configDir, "docker-env.yaml"))
	if os.IsNotExist(err) {
		return c
	}

	if err != nil {
		panic(err)
	}

	err = yaml.Unmarshal(raw, &c)

	if err != nil {
		panic(err)
	}

	return c

}

func (p Config) Sanitize() Config {
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
