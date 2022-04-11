package router

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"

	"github.com/gorilla/mux"
	"github.com/shawnburke/docker-env/backend/spaces"
)

var manager spaces.Manager

type router struct {
	*mux.Router
	manager spaces.Manager
}

func New(manager spaces.Manager) http.Handler {

	r := mux.NewRouter()

	ret := &router{
		Router:  r,
		manager: manager,
	}

	r.Use(loggingMiddleware)

	spaces := r.PathPrefix("/spaces").Subrouter()
	spaces.HandleFunc("/{user}", ret.createSpace).Methods("POST")
	spaces.HandleFunc("/{user}", ret.listSpaces).Methods("GET")
	spaces.HandleFunc("/{user}/{name}", ret.getSpace).Methods("GET")
	spaces.HandleFunc("/{user}/{name}", ret.removeSpace).Methods("DELETE")

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
}

func (r *router) createSpace(w http.ResponseWriter, req *http.Request) {
	vars := mux.Vars(req)
	user := vars["user"]

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
	}

	success, output, err := r.manager.Create(s)

	if os.IsExist(err) {
		w.WriteHeader(409)
		return
	}

	if err != nil || !success {
		w.WriteHeader(500)
		w.Write([]byte(fmt.Sprintf("Error creating: %v\n", err)))
		w.Write([]byte(output))
		return
	}

	instance, err := r.manager.Get(csr.User, csr.Name, false)
	if err != nil {
		w.WriteHeader(500)
		w.Write([]byte(fmt.Sprintf("Error getting after create: %v", err)))
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

func (r *router) listSpaces(w http.ResponseWriter, req *http.Request) {

	vars := mux.Vars(req)
	user := vars["user"]

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

func (r *router) getSpace(w http.ResponseWriter, req *http.Request) {

	vars := mux.Vars(req)
	user := vars["user"]
	name := vars["name"]

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

func (r *router) removeSpace(w http.ResponseWriter, req *http.Request) {

	vars := mux.Vars(req)
	user := vars["user"]
	name := vars["name"]

	err := r.manager.Kill(user, name)

	if os.IsNotExist(err) {
		w.WriteHeader(404)
		return
	}
}
