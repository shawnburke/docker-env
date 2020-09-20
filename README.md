# Docker-based development env

Quick and dirty way to host docker-based development enviornments that can be accessed via SSH or VSCode remote.

Mostly a project to understand and learn what it takes to host an environment.

The containers will have a home directory that is mounted external (at ./home of this dir) so things here will persist across restarts.

## Setup

You can use the Dockerfile at `./build/Dockerfile` or customize it, but it must preseve the end part that sets up user, ssh, etc.

## Commands

The `docker-env.sh` command allows building, starting, and upgrading containers.

### docker-env.sh build

Builds or rebuilds the container.

### docker-env.sh start user-name [container name]

`start` starts a container for the given user.  It assumes this user exists on the host.

Optionally you can pass a second arg to specify the container name.  Else it defaults to `user_env`, like "shawn_env"

This will output the port for the newly created container.

### docker-env.sh upgrade

Updates all running containers to the latest build and then restarts them.

## Usage

Start a container then you can SSH to it like `ssh -a -p [port]`.  Likewise you can connect using VSCode remote.

