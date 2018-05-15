#FROM forwardloop/floop-host-debian-jessie-python36-dockermachine
#RUN apt-get update && apt-get install -y rsync
#WORKDIR /floop
#RUN wget -O virtualbox.deb https://download.virtualbox.org/virtualbox/5.2.10/virtualbox-5.2_5.2.10-122088~Debian~jessie_amd64.deb
#RUN wget -O virtualbox.deb https://download.virtualbox.org/virtualbox/5.1.36/virtualbox-5.1_5.1.36-122089~Debian~jessie_amd64.deb 
#RUN apt-get install -y gdebi
#RUN gdebi --non-interactive virtualbox.deb
FROM jencryzthers/vboxinsidedocker
RUN apt-get update && apt-get install -y curl
RUN base=https://github.com/docker/machine/releases/download/v0.14.0 && \
  curl -L $base/docker-machine-$(uname -s)-$(uname -m) >/root/docker-machine
RUN install /root/docker-machine /usr/local/bin/docker-machine
