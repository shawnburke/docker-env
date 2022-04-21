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

Let's imagine our  server is in our ssh config as `env-server` and you have access to it via `ssh env-server`.

This is the server you ran the above steps on.

Now, on a client.

1. Clone this repo
2. `cd client`
3. Connect to the API: `./docker-env env-server`.  
4. Create a developer enviornment: `env-server> create devbox`.  This will create a server for you to use:

```
❯ env-server> create devbox
Created devbox
	SSH Port: 35385
    Run `connect devbox` to start tunnels
```

Here the environment is running, so we set up our local ports to access it.

5. `> connect devbox`

```
❯ > connect devbox
Connected SSH as localhost:35385
```

Success! We've now connected!

## Accessing the instance via SSH

To SSH to the instance, run `env-server>  ssh devbox`.  This will give you an SSH prompt to the box:

```
env-server> ssh demo
ssh -A -p 35385 sburke@localhost
Welcome to Ubuntu 20.04.4 LTS (GNU/Linux 5.4.0-1041-aws x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

This system has been minimized by removing packages and content that are
not required on a system that users do not log into.

To restore this content, you can run the 'unminimize' command.
Last login: Thu Apr 21 03:11:23 2022 from 172.24.0.1
sburke@sburke-demo:~$ 
```

Note the raw SSH command is printed at the top if you want to do the same outside of the instance.

## Accessing with tools

### Visual Studio Code Remote
To access with VSCode, ensure you have the "Remote SSH" extension installed.

1. Command Palette >> "Remote SSH Connect to Host..."
2. Use the SSH port from above `localhost:35385`

### Accessing with IntelliJ Remote
IntelliJ support is already installed in the base image.

First, SSH to your instance and clone whatever code you plan to work on.


1. Install [JetBrains Remote Gateway](https://www.jetbrains.com/remote-development/gateway/)
2. Once you run the client choose "Remote-Development >> SSH"
3. Configure a new connection with your username, `localhost`, and the SSH port (the SSH port entry field is a bit weird, but you can get it to work)
4. Hit OK and choose the folder you cloned above, and which tool you intend to use
5. Go!

### Accessing In-Browser VSCode

VSCode in-browser support is already provided using the Coder.com [Code Server](https://github.com/coder/code-server) project.

1. SSH to your instance
2. Run `start-code-server`
3. After a few seconds you'll see output that the client (assuming it has done `connect [name]`) has noticed the new port:

```
Connected VSCode Browser as localhost:59564
        Connect to VSCode browser at http://localhost:59564
```

Click on that link and you're off and running!

### Accessing with In-Browser IDEA

This works best if you open a second instance of the client.

1. In the client, ssh to your instance
2. Run `projector run`, which will take you through the install steps for [JetBrains Projector](https://lp.jetbrains.com/projector/)
3. Once its running, you'll see that the port has been noticed by the client:

```
kraken-dev-941> 
Connected IntelliJ Projector as localhost:60669
        Connect to IntelliJ browser at http://localhost:60669
```

Click the link and off you go.  

Once you have done the above once, you can make it run in the background via `nohup projector run &`

Enjoy!