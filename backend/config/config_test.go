package config

import (
	"fmt"
	"io/ioutil"
	"os"
	"path"
	"testing"
	"time"

	"github.com/stretchr/testify/require"
)

func createConfig(t *testing.T, yaml string) string {

	configDir := path.Join(os.TempDir(), fmt.Sprintf("%d", time.Now().UnixMicro()))

	err := os.MkdirAll(configDir, os.ModeDir|os.ModePerm)
	require.NoError(t, err)

	p := path.Join(configDir, configFileName)
	err = ioutil.WriteFile(p, []byte(yaml), 0644)
	require.NoError(t, err)

	return configDir

}

func TestLoadYaml(t *testing.T) {

	yamlFile := `
dir: /some/dir
dns_copy_from_host: true
dns_nameservers:
- 1.1.1.1
- 2.2.2.2
`

	configDir := createConfig(t, yamlFile)
	c := Load(configDir)

	require.Equal(t, true, c.DnsCopyFromHost)
	require.Len(t, c.DnsNameservers, 2)
	require.Equal(t, "2.2.2.2", c.DnsNameservers[1])

	require.Equal(t, c.Dir, "/some/dir")

}

func TestLoadYamlOverride(t *testing.T) {

	yamlFile := `
dir: /some/dir
port: 1234
`

	os.Setenv("PORT", "4321")
	os.Setenv("DIR", "/other/dir")
	configDir := createConfig(t, yamlFile)
	c := Load(configDir)

	require.Equal(t, 4321, c.Port)
	require.Equal(t, "/other/dir", c.Dir)

}
