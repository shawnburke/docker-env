# Docker-Based Remote Servers

This is a toolset that allows running remote development environments via docker.

Each environment:

1. Is a container is provisioned with whatever tools are needed by developers. Container images are centrally managed allowing adminsitrative curation.  The only hard requirement is that the container has a running SSH server.
2. The container setup is created for each user.  User's home directory is persisted to a docker volume that survives container restarts.  Each container gets it own docker 
socket so they do not conflict with each other, etc.
3. Environments can be managed using a CLI included in the `client` folder.

With a full image, you get support for VSCode Remote, JetBrains Remote Gateway, and in-browser VSCode and IDEA Projector, built in.

## Setup Server

To set up a server, you just need an instance that supports SSH and Docker.

1. Clone this repo
2. Run `standup` in the root.  This will build the docker containers, then build and start the server on port `3001` in your host.


## Accessing with Client

To create an environment, you need to be able to access the server via SSH.

Let's imagine our server is `server.my-company.com` and you have access to it via `ssh server.my-company.com`.

This is the server you ran the above steps on.

Now, on a client.

1. Clone this repo
2. `cd client`
3. Connect to the API: `./docker-env connect api server.my-company.com`.  This will create an SSH tunnel on port `3001` to allow access to the server API.
4. Create a developer enviornment: `./docker-env create devbox`.  This will create a server for you to use:

```
❯ ./docker-env create devbox
Created devbox
	SSH Port: 35385
    Run `docker-env connect devbox` to start tunnels
```

Here the environment is running, so we set up our local ports to access it.

5. `./docker-env connect devbox`

```
❯ ./docker-env connect devbox
Connected SSH as localhost:35385
	Command: ssh -NL 35385:localhost:35385 kraken-dev-s466
```

Success! We've now connected!

6. SSH to the instance `./docker-env ssh devbox`.  This will give you an SSH prompt.

Here you can also run VSCode or JetBrains remote using the SSH access.  

Enjoy!