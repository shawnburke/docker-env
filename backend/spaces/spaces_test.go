package spaces

import (
	"net"
	"os"
	"path"
	"strconv"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/require"
)

func TestWriteFiles(t *testing.T) {
	// pwd, err := os.Getwd()
	// require.NoError(t, err)
	dir := path.Join(os.TempDir(), ".tmp", "docker-env")
	err := os.MkdirAll(dir, os.ModeDir|os.ModePerm)
	require.NoError(t, err)

	s := NewSpace{
		User:     "the-user",
		Password: "the-password",
		Name:     "the-space",
	}

	err = createSpaceFiles(dir, s)
	require.NoError(t, err)

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
