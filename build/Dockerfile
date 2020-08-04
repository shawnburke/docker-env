#-----------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for license information.
#-----------------------------------------------------------------------------------------

FROM golang:latest


# Verify git, process tools installed
RUN apt-get update && apt-get -yq install git procps ftp sqlite3 build-essential tzdata python-pip ffmpeg openssh-server
RUN pip install amcrest

RUN curl -sL https://deb.nodesource.com/setup_14.x | bash - && apt-get install -y nodejs

RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg |  apt-key add - && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" |  tee /etc/apt/sources.list.d/yarn.list

RUN npm install -g browserify watchify yarn

# Clean up
RUN apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/*


ARG ROOTPASSWORD=linuxdev

RUN mkdir /var/run/sshd
RUN echo 'root:$ROOTPASSWORD' | chpasswd
RUN sed -i 's/PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# SSH login fix. Otherwise user is kicked off after login
RUN sed 's@session\s*required\s*pam_loginuid.so@session optional pam_loginuid.so@g' -i /etc/pam.d/sshd

ENV NOTVISIBLE "in users profile"
RUN echo "export VISIBLE=now" >> /etc/profile
COPY init_user.sh /root
copy entrypoint.sh /root

EXPOSE 22

ENV ENV_USER=""

CMD ["/root/entrypoint.sh"]
