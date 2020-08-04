#! /bin/bash


if [ -z "$ENV_USER" ]
then
    echo "User is not set!"
    exit 1
fi

# Ensure user is set up.
/root/init_user.sh $ENV_USER


echo "Starting SSH server"
/usr/sbin/sshd -D