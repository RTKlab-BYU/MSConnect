FROM ubuntu:22.04
LABEL maintainer = Xiaofeng Xie xiexf128@gmail.com
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt install -y git
RUN apt install -y rsync
RUN apt-get -y install python3 python3-pip python3-venv python3-wheel wget 
RUN apt-get install -y --no-install-recommends p7zip-full

# install docker-ce-cli
RUN  apt-get install -y ca-certificates curl gnupg
RUN install -m 0755 -d /etc/apt/keyrings
RUN curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
RUN chmod a+r /etc/apt/keyrings/docker.gpg
RUN echo \
    "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
    "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | \
    tee /etc/apt/sources.list.d/docker.list > /dev/null
RUN apt-get update
RUN apt-get install -y docker-ce-cli

#set up locale
RUN apt update && apt -y install locales && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
WORKDIR /app

#set up python environment
ENV VIRTUAL_ENV=/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH" 
COPY requirements.txt requirements.txt
RUN /venv/bin/pip install -r requirements.txt
RUN /venv/bin/pip install uwsgi

#set up R
RUN wget -qO- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc | gpg --dearmor -o /usr/share/keyrings/r-project.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/r-project.gpg] https://cloud.r-project.org/bin/linux/ubuntu jammy-cran40/" | tee -a /etc/apt/sources.list.d/r-project.list
RUN apt update
RUN apt-get install  -y r-base-dev
RUN apt-get install -y libxml2-dev
RUN apt-get install -y r-cran-devtools

#set up R environment for Juipter Nootebook
COPY install.R install.R
RUN Rscript /app/install.R 

COPY . .

CMD ["/venv/bin/uwsgi", "--ini", "/app/datamanager.uwsgi.ini"]
