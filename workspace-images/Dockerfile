from docker-env-base:local


## Setup Node
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - && apt-get install -y nodejs

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg |  apt-key add - && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" |  tee /etc/apt/sources.list.d/yarn.list

RUN npm install -g browserify watchify yarn

# setup Go

RUN curl -OL https://go.dev/dl/go1.18.1.linux-amd64.tar.gz
RUN tar -C /usr/local -xvf go1.18.1.linux-amd64.tar.gz
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


# Install java versions 11 & 17
RUN wget -O jdk17.tar.gz https://download.java.net/java/GA/jdk17.0.2/dfd4a8d0985749f896bed50d7138ee7f/8/GPL/openjdk-17.0.2_linux-x64_bin.tar.gz && tar xvf jdk17.tar.gz && mv jdk-17.0.2/ /opt/jdk-17/
RUN wget -O jdk11.tar.gz https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_linux-x64_bin.tar.gz && tar xvf jdk11.tar.gz && mv jdk-11.0.2/ /opt/jdk-11/
RUN ln -s /opt/jdk-17 /opt/java
RUN ln -s /opt/java/bin/java /usr/local/bin/java

ENV JAVA_HOME=/opt/java
ENV PATH="$JAVA_HOME/bin:$PATH"

RUN grep JAVA_HOME /etc/environment || printf "JAVA_HOME=/opt/java\nPATH=$JAVA_HOME/bin:$PATH\n" >> /etc/environment

# Clean up
RUN apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*



