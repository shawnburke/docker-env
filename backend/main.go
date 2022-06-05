package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"strings"

	"github.com/shawnburke/docker-env/backend/router"
	"github.com/shawnburke/docker-env/backend/spaces"
	"gopkg.in/yaml.v3"
)

func main() {

	port := 3001

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
		CopyHostDns:    os.Getenv("COPY_HOST_DNS") == "true" || os.Getenv("COPY_HOST_DNS") == "1",
		DnsNameservers: strings.Split(os.Getenv("DNS_NAMESERVERS"), ","),
	}

	raw, err := yaml.Marshal(params)
	if err != nil {
		panic(err)
	}

	log.Printf("Config:\n%v\n", string(raw))

	manager := spaces.New(params)
	mux := router.New(manager)
	fmt.Println("Starting server on port: ", port)
	fmt.Println("Using dir: ", dir)
	err = http.ListenAndServe(fmt.Sprintf("0.0.0.0:%d", port), mux)
	if err != nil {
		log.Printf("Error starting HTTP server: %v", err)
	}
}
