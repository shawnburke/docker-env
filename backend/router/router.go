package router

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
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

	spaces := r.PathPrefix("/spaces").Subrouter()
	spaces.HandleFunc("/{user}", ret.createSpace).Methods("POST")
	spaces.HandleFunc("/{user}", ret.listSpaces).Methods("GET")
	spaces.HandleFunc("/{user}/{name}", ret.getSpace).Methods("GET")
	spaces.HandleFunc("/{user}/{name}", ret.removeSpace).Methods("DELETE")

	return ret
}

type createSpaceRequest struct {
	User     string `json:"user"`
	Name     string `json:"name"`
	Password string `json:"password"`
	PubKey   string `json:"pub_key"`
}

func (r *router) createSpace(w http.ResponseWriter, req *http.Request) {
	vars := mux.Vars(req)
	user := vars["user"]
	fmt.Printf("POST /spaces/%s", user)

	csr := &createSpaceRequest{}

	body, err := ioutil.ReadAll(req.Body)
	if err != nil {
		w.Write([]byte(err.Error()))
		w.WriteHeader(500)
		return
	}

	err = json.Unmarshal(body, csr)
	if err != nil {
		w.Write([]byte(fmt.Sprintf("Can't unmarshal: %v\n%s"+err.Error(), string(body))))
		w.WriteHeader(400)
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
		w.Write([]byte(fmt.Sprintf("Error creating: %v\n", err)))
		w.Write([]byte(output))
		w.WriteHeader(500)
		return
	}

	instance, err := r.manager.Get(csr.User, csr.Name, false)
	if err != nil {
		w.Write([]byte(fmt.Sprintf("Error getting after create: %v", err)))
		w.WriteHeader(500)
		return
	}

	raw, err := json.Marshal(instance)
	if err != nil {
		w.Write([]byte(fmt.Sprintf("Error marshalling: %v", err)))
		w.WriteHeader(500)
		return
	}
	w.Write(raw)

	w.Header().Add("Location", fmt.Sprintf("http://localhost:%v/spaces/%s/%s", 3000, user, csr.Name))
	w.WriteHeader(201)
}

func (r *router) listSpaces(w http.ResponseWriter, req *http.Request) {

	vars := mux.Vars(req)
	user := vars["user"]

	instances, err := r.manager.List(user)

	raw, err := json.Marshal(instances)

	if err != nil {
		w.Write([]byte(fmt.Sprintf("Error marshalling: %v", err)))
		w.WriteHeader(500)
		return
	}

	w.Write(raw)
	w.Header().Add("Content-Type", "application/json")
	w.WriteHeader(200)
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
		w.Write([]byte(fmt.Sprintf("Error marshalling: %v", err)))
		w.WriteHeader(500)
		return
	}

	raw, err := json.Marshal(instance)

	if err != nil {
		w.Write([]byte(fmt.Sprintf("Error marshalling: %v", err)))
		w.WriteHeader(500)
		return
	}

	w.Write(raw)
	w.Header().Add("Content-Type", "application/json")
	w.WriteHeader(200)
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

	w.WriteHeader(200)
}
