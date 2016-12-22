FROM ubuntu:16.04

RUN apt-get -yqq update && \
    apt-get -yqq install python python-nose python-zmq ipython python-numpy \
                         python-scipy python-netcdf4 python-matplotlib \
                         python-mpltoolkits.basemap python-pip apache2 \
                         libapache2-mod-wsgi python-setuptools python-lxml \
                         git-core && \
    pip install threddsclient

RUN cd /root && \
    git clone https://github.com/geopython/PyWPS.git && \
    cd /root/PyWPS && \
    python setup.py install && \
    mkdir /var/www/html/wps && \
    mkdir /var/www/html/wps_results && \
    useradd apapywps && \
    mkdir /home/apapywps && \
    chown apapywps /home/apapywps && \
    chgrp apapywps /home/apapywps && \
    chown apapywps /var/www/html/wps_results && \
    chgrp apapywps /var/www/html/wps_results && \
    rm -rf /root/PyWPS && \
    cd /root && \
    git clone -b wps-processes https://github.com/Ouranosinc/PAVICS.git && \
    cd /root/PAVICS && \
    python setup.py install && \
    rm -rf /root/PAVICS

COPY pywps.wsgi /var/www/html/wps/
COPY apache2.conf /etc/apache2/
COPY pywps.cfg /etc/
COPY wps_processes/wps_*.py /var/www/html/wps/

CMD printf "\nexport SOLR_HOST=$SOLR_HOST\n" >> /etc/apache2/envvars && \
    printf "\nexport SOLR_PORT=$SOLR_PORT\n" >> /etc/apache2/envvars && \
    printf "\nexport THREDDS_HOST=$THREDDS_HOST\n" >> /etc/apache2/envvars && \
    printf "\nexport THREDDS_PORT=$THREDDS_PORT\n" >> /etc/apache2/envvars && \
    printf "\nexport OPENSTACK_INTERNAL_IP=$OPENSTACK_INTERNAL_IP\n" >> /etc/apache2/envvars && \
    sed -i '/outputurl=/c\outputurl=http://'"$WPS_HOST"':'"$WPS_PORT"'/wps_results/' /etc/pywps.cfg && \
    /etc/init.d/apache2 start && tail -f /dev/null

EXPOSE 80
