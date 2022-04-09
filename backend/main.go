package main

import (
	"fmt"
	"net/http"
	"os"
	"strconv"

	"github.com/shawnburke/docker-env/backend/router"
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

	mux := router.New()
	fmt.Println("Starting server on port: ", port)
	http.ListenAndServe(fmt.Sprintf("0.0.0.0:%d", port), mux)
}
