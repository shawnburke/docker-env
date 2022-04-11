
#! /bin/bash
# check arg
echo "Setting up user $1"

if [ -z "$1" ]
then
	echo "No user set!"
	exit 1
fi

u=$1
homedir=/home/$u
if cat /etc/passwd | grep -oE "^$u:" < /dev/null
then
	echo "User exists"
	exit 0
else
  if ! useradd -d $homedir $u
  then
	echo "User exists (code=$?)"
	exit 0
  fi
  usermod -aG sudo $u
  usermod -s /bin/bash $u

  [[ -d /etc/skel && ! -f $homedir/.bashrc ]] && cp /etc/skel/.* $homedir
fi

password=$u

if [ -n "$2" ]
then
  password=$2
fi

# set up the authorized keys file so that the
# host machine can securely SSH in for same user
cd $homedir
mkdir -p $homedir/.ssh
if [[ -f /tmp/pubkey && ! -f $homedir/.ssh/authorized_keys ]]
then
	cat /tmp/pubkey >> $homedir/.ssh/authorized_keys
	chmod 600 .ssh/authorized_keys
fi

chown -R $1:$1 $homedir

# HACK: set password async because it 
# fails if done during entry point
bash -c "sleep 1; printf \"$password\n$password\" | passwd $u; echo \"passwd set to $password\"" &


