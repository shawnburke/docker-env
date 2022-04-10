package router

import (
	"encoding/json"
	"io/ioutil"
	"net/http"
	"os"

	"github.com/gorilla/mux"
	"github.com/shawnburke/docker-env/backend/spaces"
)

var manager spaces.Manager

func New() *mux.Router {

	r := mux.NewRouter()

	spaces := r.PathPrefix("/spaces").Subrouter()
	spaces.HandleFunc("/{user}/spaces", createSpace).Methods("POST")
	//	spaces.HandleFunc("/{user}/spaces", getSpacesForUser).Methods("GET")
	spaces.HandleFunc("/{user}/spaces/{name}", getSpace).Methods("GET")
	return r
}

type createSpaceRequest struct {
	User     string `json:"user"`
	Name     string `json:"name"`
	Password string `json:"password"`
	PubKey   string `json:"pub_key"`
}

func createSpace(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	user := vars["user"]

	req := &createSpaceRequest{}

	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		w.Write([]byte(err.Error()))
		w.WriteHeader(500)
		return
	}

	err = json.Unmarshal(body, req)
	if err != nil {
		w.Write([]byte("Can't unmarshal: " + err.Error()))
		w.WriteHeader(400)
		return
	}

	s := spaces.NewSpace{
		User:     user,
		Name:     req.Name,
		PubKey:   req.PubKey,
		Password: req.Password,
	}

	pwd, err := os.Getwd()
	if err != nil {
		panic(err)
	}

	manager := spaces.New(pwd)
	exists, output, err := manager.Create(s)

	if exists {
		w.WriteHeader(409)
		return
	}

	w.Write([]byte(output))
	w.WriteHeader(202)
}

func getSpace(w http.ResponseWriter, r *http.Request) {
	// vars := mux.Vars(r)
	// user := vars["user"]
	// space := vars["space"]

	panic("NYI")
}
