FROM ubuntu:16.04

RUN apt-get -yqq update && \
    apt-get -yqq install python python-nose python-zmq ipython python-numpy \
                         python-scipy python-netcdf4 python-matplotlib \
                         python-mpltoolkits.basemap python-pip apache2 \
                         libapache2-mod-wsgi python-setuptools python-lxml \
                         git-core && \
    pip install threddsclient

COPY pywps_patch /root

RUN cd /root && \
    git clone https://github.com/geopython/PyWPS.git && \
    cd /root/PyWPS && \
    git reset --hard 8bcea628d22f36dd50a2b9f49cdd7f1d63aea825 && \
    patch /root/PyWPS/pywps/app/Service.py /root/pywps_patch && \
    python setup.py install && \
    mkdir /var/www/html/wps && \
    mkdir /var/www/html/wps_results && \
    useradd apapywps && \
    mkdir /home/apapywps && \
    chown apapywps /home/apapywps && \
    chgrp apapywps /home/apapywps && \
    chown apapywps /var/www/html/wps_results && \
    chgrp apapywps /var/www/html/wps_results && \
    rm -rf /root/PyWPS /root/pywps_patch && \
    cd /root && \
    git clone -b pav133 https://github.com/Ouranosinc/PAVICS.git && \
    cp /root/PAVICS/pavics/processes/wps_*.py /var/www/html/wps/ && \
    rm -rf /root/PAVICS && \
    git clone -b pav152 https://github.com/Ouranosinc/PAVICS.git && \
    cd /root/PAVICS && \
    python setup.py install && \
    cp /root/PAVICS/pavics/processes/wps_*.py /var/www/html/wps/ && \
    rm -rf /root/PAVICS

COPY pywps.wsgi /var/www/html/wps/
COPY apache2.conf /etc/apache2/

CMD printf "\nexport SOLR_SERVER=$SOLR_SERVER\n" >> /etc/apache2/envvars && \
    printf "\nexport OPENSTACK_INTERNAL_IP=$OPENSTACK_INTERNAL_IP\n" >> /etc/apache2/envvars && \
    /etc/init.d/apache2 start && tail -f /dev/null

EXPOSE 80
