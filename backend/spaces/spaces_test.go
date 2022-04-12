package spaces

import (
	"os"
	"path"

	"github.com/stretchr/testify/require"
)

func TestWriteFiles(t require.TestingT) {
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
