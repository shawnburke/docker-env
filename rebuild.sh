#! /bin/bash

old_sha=$(docker images --format '{{.ID}}' container_dev)

# See if we need to rebuild

docker build ./build -t container_dev >/dev/null

# Check the resulting sha
sha=$(docker images --format '{{.ID}}' container_dev)
if [ "$old_sha" == "$sha" ]
then
   echo "No container change, exiting."
  exit 0
fi


# Gather all of the running containers and their users and container names

running=$(docker ps --format '{{.ID}} {{.Image}} {{.Names}} {{.Labels}}')

restart=

echo "$running" | while read p
do
   container_name=$(echo $p | awk '{print $3}')
   user_name=$(echo $p | awk '{print $4}' | grep -oE "=(.*)" | grep -oE [^=]+)
   if docker rm -f $container_name
   then
    echo "Will restart $container_name"
    restart="$restart $user_name:$container_name"
   fi
done

docker build -t container_env ./build


echo "$restart" | while read p
do
   if [ -n "$p" ]
   then
    echo "Restarting $p..."
    user=$(echo $p |      awk 'BEGIN { FS = ":" } ; { print $1 }')
    container=$(echo $p | awk 'BEGIN { FS = ":" } ; { print $2 }')
    ./start_container.sh $user $container
   fi
done

 


