#! /bin/bash
# check arg
echo "Setting up user $1"

if [ -z "$1" ]
then
	echo "No user set!"
	exit 1
fi

if ! useradd  $1
then
	echo "User exists"
	exit 0
else
  usermod -aG sudo $1
fi

pwd=$1

if [ -n "$2" ]
then
  pwd=$2
fi

# setup home dir
mkdir -p /home/$1/.ssh
cd /home/$1/.ssh

# set up the authorized keys file so that the
# host machine can securely SSH in for same user
touch authorized_keys
chmod 600 authorized_keys
chown -R $1:$1 /home/$1


usermod --shell /bin/bash $1


# HACK: set password async because it 
# fails if done during entry point
bash -c "sleep 1; printf '$1\n$1' | passwd shawn; echo 'passwd set'" &


