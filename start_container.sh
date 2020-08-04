#! /bin/bash

if [ -z "$1" ] 
then
  echo "user name required"
  exit 1
fi 

force=$([ "$2" == "-f" ] && echo "true")

#
# Setup vars
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
if current_state=$(docker inspect $container_name --format '{{.State.Status}}')
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
if  docker rm -f $container_name
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
# init user SSH keys
#
pubkey=$(cat ~/.ssh/id_rsa.pub)
if ! grep "$pubkey" $user_home/.ssh/authorized_keys >/dev/null
then
  echo "Setting up ssh keys"
  mkdir -p $user_home/.ssh/authorized_keys
  cat ~/.ssh/id_rsa.pub >> $user_home/.ssh/authorized_keys
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

if docker run -d -P \
  --name $container_name \
  -v $user_home:/home/$user \
  -l owner=$user \
  -e ENV_USER=$user $port_arg \
  --restart unless-stopped \
  container_env:latest
then
  echo "Created container $container_name"
fi


port=$(docker port $container_name 22)
[[ -z "$existing_port" ]] && printf "$portkey\t$port\n" >> ports
echo "Running.  SSH: $port"

