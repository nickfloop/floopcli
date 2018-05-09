FROM forwardloop/floop-host-debian-jessie-python36-dockermachine
WORKDIR /floop
#RUN wget -O virtualbox.deb https://download.virtualbox.org/virtualbox/5.2.10/virtualbox-5.2_5.2.10-122088~Debian~jessie_amd64.deb
RUN wget -O virtualbox.deb https://download.virtualbox.org/virtualbox/5.1.36/virtualbox-5.1_5.1.36-122089~Debian~jessie_amd64.deb 
RUN apt-get install -y gdebi
RUN gdebi --non-interactive virtualbox.deb
