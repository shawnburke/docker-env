package router

import (
	"encoding/json"
	"net/http"

	"github.com/gorilla/mux"
	"github.com/shawnburke/docker-env/backend/spaces"
)

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
	Password string `json:"password"`
	PubKey   string `json:"pub_key"`
}

func createSpace(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	user := vars["user"]

	req := &createSpaceRequest{}

	err := json.Unmarshal(r.Body, req)
	if err != nil {
		w.Write(byte[]("Can't unmarshal: " + err.Error()))
		w.WriteHeader(400)
		return
	}

	exists, err := spaces.Start(req.User, req.Password, req.PubKey)

	if exists {
		w.WriteHeader(409)
		return
	}

	panic("NYI")
}

func getSpace(w http.ResponseWriter, r *http.Request) {
	// vars := mux.Vars(r)
	// user := vars["user"]
	// space := vars["space"]

	panic("NYI")
}
