#! /bin/bash


if [ -z "$ENV_USER" ]
then
    echo "User is not set!"
    exit 1
fi

# Ensure user is set up.
echo "ENSURING USER: $ENV_USER"
/root/ensure_user.sh $ENV_USER $ENV_USER_PASSWORD $ENV_USER_PUBKEY

echo "Starting SSH server"
mkdir -p -m0755 /var/run/sshd
/usr/sbin/sshd -D