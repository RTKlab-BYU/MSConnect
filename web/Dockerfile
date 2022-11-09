FROM ubuntu:22.04
LABEL maintainer = Xiaofeng Xie xiexf128@gmail.com
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get -y install python3 python3-pip python3-venv python3-wheel wget 
RUN apt-get install -y --no-install-recommends p7zip-full
RUN apt-get install -y mono-complete
RUN wget https://download.docker.com/linux/ubuntu/dists/jammy/pool/stable/amd64/docker-ce-cli_20.10.21~3-0~ubuntu-jammy_amd64.deb
RUN dpkg -i docker-ce-cli_20.10.21~3-0~ubuntu-jammy_amd64.deb
RUN rm docker-ce-cli_20.10.21~3-0~ubuntu-jammy_amd64.deb
#for R
RUN wget -qO- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc | gpg --dearmor -o /usr/share/keyrings/r-project.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/r-project.gpg] https://cloud.r-project.org/bin/linux/ubuntu jammy-cran40/" | tee -a /etc/apt/sources.list.d/r-project.list
RUN apt update
RUN apt install -y --no-install-recommends r-base

RUN python3 -m venv venv
RUN apt update && apt -y install locales && locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8
WORKDIR /app
COPY requirements.txt requirements.txt
RUN /venv/bin/pip install -r requirements.txt
RUN /venv/bin/pip install uwsgi
#RUN /venv/bin/pip install --upgrade requests

COPY . .
#RUN /venv/bin/activate
#EXPOSE 8000
CMD ["/venv/bin/uwsgi", "--ini", "/app/datamanager.uwsgi.ini"]
# RUN python3 manage.py runserver 0.0.0.0:8000

#RUN chmod +x /app/start.sh
#ENTRYPOINT ["./start.sh"]