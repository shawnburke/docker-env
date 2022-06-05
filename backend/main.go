package main

import (
	"fmt"
	"log"
	"net/http"

	"github.com/shawnburke/docker-env/backend/config"
	"github.com/shawnburke/docker-env/backend/router"
	"github.com/shawnburke/docker-env/backend/spaces"
	"gopkg.in/yaml.v3"
)

func main() {

	// loads a config file called docker-env.yaml from
	// the current working dir
	cfg := config.Load("")
	raw, err := yaml.Marshal(cfg)
	if err != nil {
		panic(err)
	}

	log.Printf("Config:\n\n%v\n", string(raw))

	manager := spaces.New(cfg)
	mux := router.New(manager)
	fmt.Println("Starting server on port: ", cfg.Port)
	err = http.ListenAndServe(fmt.Sprintf("0.0.0.0:%d", cfg.Port), mux)
	if err != nil {
		log.Printf("Error starting HTTP server: %v", err)
	}
}
