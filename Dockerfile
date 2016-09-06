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
    patch /root/PyWPS/pywps/app/Service.py /root/pywps_patch && \
    cd /root/PyWPS && \
    python setup.py install && \
    cd /root && \
    git clone -b pav133 https://github.com/Ouranosinc/PAVICS.git && \
    mkdir /var/www/html/wps && \
    mkdir /var/www/html/wps_results && \
    chown games /var/www/html/wps_results && \
    chgrp games /var/www/html/wps_results && \
    cp /root/PAVICS/pavics/processes/wps_*.py /var/www/html/wps/ && \
    useradd apapywps && \
    mkdir /home/apapywps && \
    chown apapywps /home/apapywps && \
    chgrp apapywps /home/apapywps && \
    rm -rf /root/PyWPS /root/pywps_patch /root/PAVICS

COPY pywps.wsgi /var/www/html/wps/
COPY apache2.conf /etc/apache2/

CMD /etc/init.d/apache2 start && tail -f /dev/null

EXPOSE 8080
