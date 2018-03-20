FROM ubuntu:16.04

# The pywps master has not been tagged recently, this is the develop from
# 2017-09-27
RUN apt-get -yqq update && \
    apt-get -yqq install python python-nose python-zmq ipython python-numpy \
                         python-scipy python-netcdf4 python-matplotlib \
                         python-mpltoolkits.basemap python-pip apache2 \
                         libapache2-mod-wsgi python-setuptools python-lxml \
                         python-future python-requests git-core

RUN pip install threddsclient && \
    pip install https://github.com/geopython/pywps/archive/48d0e6b5bc5c3f31b3d5eb56341d4a66558ccd51.zip && \
    pip install https://github.com/Ouranosinc/pyPavics/archive/0.3.0.zip

COPY . /root/
COPY configtests.cfg /root/pavics_datacatalog/tests/

RUN cd /root && \
    python setup.py install && \
    python setup.py test && \
    useradd apapywps && \
    install -d -o apapywps -g apapywps /home/apapywps

COPY pywps.wsgi /var/www/html/wps/
COPY apache2.conf /etc/apache2/
COPY pywps.cfg /etc/
COPY catalog.cfg /home/
COPY docker_configs.py /home/

CMD python /home/docker_configs.py && \
    /etc/init.d/apache2 start && tail -f /dev/null

EXPOSE 80
