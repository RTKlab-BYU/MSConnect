FROM ubuntu:22.04
LABEL maintainer = Xiaofeng Xie xiexf128@gmail.com
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get -y install python3 python3-pip python3-venv python3-wheel 
RUN apt-get install -y --no-install-recommends p7zip-full
RUN apt-get install -y mono-complete
# ARG USER=root
# USER $USER
RUN python3 -m venv venv
WORKDIR /app
COPY requirements.txt requirements.txt
RUN /venv/bin/pip install -r requirements.txt
RUN /venv/bin/pip install uwsgi

COPY . .
#RUN /venv/bin/activate
#EXPOSE 8000
CMD ["/venv/bin/uwsgi", "--ini", "/app/datamanager.uwsgi.ini"]
# RUN python3 manage.py runserver 0.0.0.0:8000

#RUN chmod +x /app/start.sh
#ENTRYPOINT ["./start.sh"]