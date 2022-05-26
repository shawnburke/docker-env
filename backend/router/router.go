package router

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"strings"

	docker "github.com/docker/docker/client"
	chi "github.com/go-chi/chi/v5"
	openapi_server "github.com/shawnburke/docker-env/backend/.gen/server"
	"github.com/shawnburke/docker-env/backend/spaces"
)

var manager spaces.Manager

type router struct {
	*chi.Mux
	manager spaces.Manager
}

func New(manager spaces.Manager) http.Handler {

	r := chi.NewRouter()

	ret := &router{
		Mux:     r,
		manager: manager,
	}

	r.Use(loggingMiddleware)

	openapi_server.HandlerFromMux(ret, r)
	return ret
}

func loggingMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Do stuff here
		log.Println(r.Method, r.RequestURI)
		// Call the next handler, which can be another middleware in the chain, or the final handler.
		next.ServeHTTP(w, r)
	})
}

type createSpaceRequest struct {
	User     string `json:"user"`
	Name     string `json:"name"`
	Password string `json:"password"`
	PubKey   string `json:"pubkey"`
	Image    string `json:"image"`
}

func (r *router) GetSpacesUser(w http.ResponseWriter, req *http.Request, user string) {
	instances, err := r.manager.List(user)

	if err != nil {
		w.WriteHeader(500)
		w.Write([]byte(fmt.Sprintf("error getting: %v", err)))
		return
	}

	raw, err := json.Marshal(instances)

	if err != nil {
		w.WriteHeader(500)
		w.Write([]byte(fmt.Sprintf("Error marshalling: %v", err)))
		return
	}

	w.Write(raw)
	w.Header().Add("Content-Type", "application/json")
}

func (r *router) GetHealth(w http.ResponseWriter, req *http.Request) {
	accept := strings.ToLower(req.Header.Get("Accept"))
	switch accept {
	case "application/json":
		w.Write([]byte(`{"result":"OK"}`))
	default:
		w.Write([]byte("OK"))
	}

}

// (POST /spaces/{user})
func (r *router) PostSpacesUser(w http.ResponseWriter, req *http.Request, user string) {
	csr := &createSpaceRequest{}

	body, err := ioutil.ReadAll(req.Body)
	if err != nil {
		w.WriteHeader(500)
		w.Write([]byte(err.Error()))
		return
	}

	err = json.Unmarshal(body, csr)
	if err != nil {
		w.WriteHeader(400)
		w.Write([]byte(fmt.Sprintf("Can't unmarshal: %v\n%s"+err.Error(), string(body))))
		return
	}

	s := spaces.NewSpace{
		User:     user,
		Name:     csr.Name,
		PubKey:   csr.PubKey,
		Password: csr.Password,
		Image:    csr.Image,
	}

	instance, output, err := r.manager.Create(s)

	if os.IsExist(err) {
		w.WriteHeader(409)
		return
	}

	if docker.IsErrNotFound(err) {
		w.WriteHeader(400)
		w.Write([]byte(fmt.Sprintf(`{"error":"Specified image tag %q is not found"}`, csr.Image)))
		return
	}

	if err != nil {
		w.WriteHeader(500)
		res := map[string]string{
			"error":  fmt.Sprintf("Error creating: %v\n", err),
			"detail": output,
		}
		raw, _ := json.Marshal(res)
		w.Write(raw)
		return
	}

	raw, err := json.Marshal(instance)
	if err != nil {
		w.WriteHeader(500)
		w.Write([]byte(fmt.Sprintf("Error marshalling: %v", err)))
		return
	}
	w.WriteHeader(201)
	w.Header().Add("Location", fmt.Sprintf("http://localhost:%v/spaces/%s/%s", 3000, user, csr.Name))
	w.Write(raw)
}

// (DELETE /spaces/{user}/{name})
func (r *router) DeleteSpacesUserName(w http.ResponseWriter, req *http.Request, user string, name string) {
	err := r.manager.Kill(user, name)

	if os.IsNotExist(err) {
		w.WriteHeader(404)
		return
	}
}

// (GET /spaces/{user}/{name})
func (r *router) GetSpacesUserName(w http.ResponseWriter, req *http.Request, user string, name string) {
	instance, err := r.manager.Get(user, name, true)

	if os.IsNotExist(err) {
		w.WriteHeader(404)
		return
	}

	if err != nil {
		w.WriteHeader(500)
		w.Write([]byte(fmt.Sprintf("Error marshalling: %v", err)))
		return
	}

	raw, err := json.Marshal(instance)

	if err != nil {
		w.WriteHeader(500)
		w.Write([]byte(fmt.Sprintf("Error marshalling: %v", err)))
		return
	}

	w.WriteHeader(200)
	w.Header().Add("Content-Type", "application/json")
	w.Write(raw)
}

// (POST /spaces/{user}/{name}/restart)
func (r *router) PostSpacesUserNameRestart(w http.ResponseWriter, req *http.Request, user string, name string) {
	err := r.manager.Restart(user, name)

	if os.IsNotExist(err) {
		w.WriteHeader(404)
		return
	}

	if err != nil {
		w.WriteHeader(500)
		w.Write([]byte(err.Error()))
	}
}
