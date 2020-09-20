#! /bin/bash

set -x
command=$1
shift 1

image_name=container_env


##
## Container building
##
function do_build {
    docker build -t $image_name  ./build
}


##
## Container creation
##

function start_container {

# Starts a container for a development enviornment
#
# Args: ./start_container USERNAME [CONTAINER_NAME, default=USERNAME_env]
#
# 1. Checks if already running and exits
# 2. Sets up home directory
# 3. Copies in SSH public keys from host to container user authorized_keys
# 4. Looks for existing ports in a file called "ports", which allows restarting
#    a container but keeping its port stable across restarts
# 5. Starts a container and adds entry to the port file.

    if [ -z "$1" ] 
    then
        echo "user name required"
        exit 1
    fi 

    force=$([ "$2" == "-f" ] && echo "true")

    tag=$image_name:latest
    if [ -n "$3" ]
    then
        tag=$3
    fi


    #
    # Setup container name and other vars
    #
    user=$1
    home_root=$(pwd)/home

    container_name=$1_env

    if [ -n "$2" ]
    then
        container_name=$2
    fi

    # We home the users dir at the container name path 
    # locally so the same user can have multiple
    # containers, but we still mount as /home/$user
    user_home=$home_root/$container_name

    #
    # Check to see if already running
    #
    if current_state=$(docker inspect $container_name --format '{{.State.Status}}') 2>&1 >/dev/null
    then
        if [ "$current_state" == "running" ]
        then

            if [ "$force" != "true" ]
            then
            echo "Already running on SSH port $(docker port $container_name 22)"
            exit 0
            fi
        fi
    fi

    # Not already running, so make sure there isn't one in a stopped state, etc.
    if  docker rm -f $container_name 2>&1 >/dev/null
    then
        echo "Removed existing container $container_name"
    fi  
    

    #
    # Set up the users home dir if it doesn't exist already
    #
    if ! ls $user_home >/dev/null
    then
        mkdir -p $user_home
        cp /etc/skel/.* $user_home
    fi

    #
    # init user SSH access, by copying id_rsa.pub contents
    # into the newly created containers authorized_keys file,
    # which allows enabling private-key access by default.
    #
    if [ -f ~/.ssh/id_rsa.pub ]
    then
        pubkey=$(cat ~/.ssh/id_rsa.pub)
        if ! grep "$pubkey" $user_home/.ssh/authorized_keys >/dev/null
        then
            echo "Setting up ssh keys"
            mkdir -p $user_home/.ssh/authorized_keys
            cat ~/.ssh/id_rsa.pub >> $user_home/.ssh/authorized_keys
        fi
    fi

    # 
    # Setup and run the server itself.
    #

    # Look if we have an existing port.  We do this because
    # by default the containers will use an ephemeral port, so we
    # want that port to be stable across host/container restarts.
    #
    # Note: this isn't bullet proof. It's possible another app
    # could grab this port between runs. If so, either put that
    # app onto another port or remove this line from
    # the ports file.
    #
    # TODO: do we ever need to clean this up?
    #   sed -i 's/grep $(portkey) ports//' ports
    #
    portkey="$user::$container_name"
    existing_port=$(grep $portkey ports | awk '{printf $2}')

    port_arg=

    [[ -n "$existing_port" ]] && port_arg="-p $existing_port:22" && echo "Reusing port $existing_port"


    # do the actual docker run
    if docker run -d -P \
        --name $container_name \
        -v $user_home:/home/$user \
        -l owner=$user \
        -e ENV_USER=$user $port_arg \
        --restart unless-stopped \
        $tag
    then
        echo "Created container $container_name"
    fi

    # Reach into docker and see what port got picked for the exposed
    # SSH port, save that to the ports file.
    port=$(docker port $container_name 22)
    [[ -z "$existing_port" ]] && printf "$portkey\t$port\n" >> ports
    echo "Running.  SSH: $port"
    exit 0
}


##
## Container rebuild, upgrade, & restart
##

function upgrade_containers {
    # Rebuilds the container is necessary then restarts running
    # containers that are not up to date.
    #
    # 1. Looks for a container called container_env
    # 2. Tries to rebuild it, which will do nothing if up to date
    # 3. Gets all of the current containers running and remembers them
    # 4. Kills the ones that need to be restarted
    # 5. Restarts them with new build

    old_sha=$(docker inspect --format '{{.ID}}' $image_name)

    # See if we need to rebuild
    echo "Attempting rebuild..."
    do_build

    # Check the resulting sha from the build
    sha=$(docker inspect --format '{{.Id}}' $image_name)


    marker=docker-env

    # Gather all of the running containers and their users and container names
    #
    running=$(docker ps --format '{{.ID}} {{.Image}} {{.Names}} {{.Labels}}' --filter "label=$marker")

    # outputexample
    # 30402c576517 container_env:latest shawn_env owner=shawn
    if [ -z "$running" ]
    then
        echo "No running instances."
        exit 0
    fi
    
    restart=
    echo "Killing existing instances..."
    echo "$running" | while read p
    do

        # The name of the container usually USER_env
        container_name=$(echo $p | awk '{print $3}')
        container_id=$(echo $p | awk '{print $1}')
        
        user_name=$(echo $p | awk '{print $4}' | grep -oE "owner=([^,]+)" | awk 'BEGIN {FS="="};{print $2}')

        # See if its up to date
        container_sha=$(docker inspect --format '{{.Image}}' $container_id)

        if [ "$container_sha" != "$sha" ]
        then
            # force remove it
            echo Removing $container_name
            if docker rm -f $container_name
            then
                echo "Restarting $container_name"
                start_container $user_name $container_name
            fi
        fi
    done
}


case $command in

  build)
    do_build
    ;;

  start)
    start_container $1 $2 $3
    ;;

  upgrade)
    upgrade_containers
    ;;

  *)
    printf "Usage: docker-env [command]\nCommands:\n"
    printf "\tbuild - build new container\n"
    printf "\tcreate [username] [container-name, default=user_env] - create new continer for user, with optional name]\n"
    printf "\tupgrade - rebuild and restart all containers not on current version\n"
    exit 1
    ;;
esac