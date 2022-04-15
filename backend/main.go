package main

import (
	"fmt"
	"net/http"
	"os"
	"strconv"
	"strings"

	"github.com/shawnburke/docker-env/backend/router"
	"github.com/shawnburke/docker-env/backend/spaces"
)

func main() {

	port := 3000

	if env := os.Getenv("PORT"); env != "" {
		p, err := strconv.ParseInt(env, 10, 32)
		if err != nil {
			panic(err)
		}
		port = int(p)
	}

	dir, err := os.Getwd()

	if err != nil {
		panic(err)
	}

	if env := os.Getenv("DIR"); env != "" {
		dir = env
	}

	os.MkdirAll(dir, os.ModeDir|os.ModePerm)

	params := spaces.Params{
		Dir:            os.Getenv("DIR"),
		DefaultImage:   os.Getenv("DEFAULT_IMAGE"),
		DnsSearch:      os.Getenv("DNS_SEARCH"),
		DnsNameservers: strings.Split(os.Getenv("DNS_NAMESERVERS"), ","),
	}

	manager := spaces.New(params)
	mux := router.New(manager)
	fmt.Println("Starting server on port: ", port)
	fmt.Println("Using dir: ", dir)
	http.ListenAndServe(fmt.Sprintf("0.0.0.0:%d", port), mux)
}
