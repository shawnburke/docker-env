from docker-env-base:local


## Setup Node
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - && apt-get install -y nodejs

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg |  apt-key add - && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" |  tee /etc/apt/sources.list.d/yarn.list

RUN npm install -g browserify watchify yarn

# setup Go

RUN curl -OL https://golang.org/dl/go1.16.7.linux-amd64.tar.gz
RUN tar -C /usr/local -xvf go1.16.7.linux-amd64.tar.gz
RUN ln -s /usr/local/go/bin/go /usr/local/bin/go

# setup Java


ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata curl ca-certificates fontconfig locales \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

ENV LANG='en_US.UTF-8' LANGUAGE='en_US:en' LC_ALL='en_US.UTF-8'

RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends tzdata curl ca-certificates fontconfig locales \
    && echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \
    && locale-gen en_US.UTF-8 \
    && rm -rf /var/lib/apt/lists/*


RUN wget https://download.java.net/java/GA/jdk17.0.2/dfd4a8d0985749f896bed50d7138ee7f/8/GPL/openjdk-17.0.2_linux-x64_bin.tar.gz && tar xvf openjdk-17.0.2_linux-x64_bin.tar.gz && mv jdk-17.0.2/ /opt/jdk-17/




ENV JAVA_HOME=/opt/jdk-17
ENV PATH="$JAVA_HOME/bin:$PATH"

RUN echo "JAVA_HOME=$JAVA_HOME" >> /etc/environment
RUN echo "PATH=$JAVA_HOME/bin:$PATH" >> /etc/environment


# # Install IntelliJ stuff

# # Run everything as root
USER root

# Packages required for multi-editor support
# RUN apt-get install -yq \
#     libxtst6 \
#     libxrender1 \
#     libfontconfig1 \
#     libxi6 \
#     libgtk-3-0

# Install intellij
RUN mkdir -p /opt/idea
RUN curl -L "https://download.jetbrains.com/product?code=IIC&latest&distribution=linux" | tar -C /opt/idea --strip-components 1 -xzvf -

# # Add a binary to the PATH that points to the intellij startup script.
RUN ln -s /opt/idea/bin/idea.sh /usr/bin/intellij-idea-community


# Add VSCode-server
RUN curl -fsSL https://code-server.dev/install.sh | sh
COPY start-code-server /usr/local/bin
RUN chmod +x /usr/local/bin/start-code-server
COPY install-projector /usr/local/bin
RUN chmod +x /usr/local/bin/install-projector


# Clean up
RUN apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*



