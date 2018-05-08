FROM forwardloop/floop-host-debian-jessie-python36-dockermachine
RUN wget -O virtualbox.deb https://download.virtualbox.org/virtualbox/5.2.10/virtualbox-5.2_5.2.10-122088~Debian~jessie_amd64.deb
RUN dpkg -i virtualbox.deb || true
RUN apt-get install -f -y
WORKDIR /floop
