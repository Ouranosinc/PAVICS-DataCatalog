FROM ubuntu:16.04

# The pywps master has not been tagged recently, this is the master from
# 2017-06-04
RUN apt-get -yqq update && \
    apt-get -yqq install python python-nose python-zmq ipython python-numpy \
                         python-scipy python-netcdf4 python-matplotlib \
                         python-mpltoolkits.basemap python-pip apache2 \
                         libapache2-mod-wsgi python-setuptools python-lxml \
                         python-future python-requests git-core postgresql \
                         python-psycopg2 && \
    pip install threddsclient && \
    pip install https://github.com/bstdenis/pywps/archive/7cab3866e34ce24d3df56e3c1c546739b1cda2d7.zip && \
    pip install https://github.com/Ouranosinc/pyPavics/archive/0.1.0.zip

COPY . /root/
COPY configtests.cfg /root/pavics_datacatalog/tests/

RUN cd /root && \
    python setup.py install && \
    python setup.py test && \
    useradd apapywps && \
    install -d -o apapywps -g apapywps /home/apapywps

USER postgres

RUN /etc/init.d/postgresql restart && \
    createuser apapywps && \
    createdb -O apapywps pywpslog

USER root

COPY pywps.wsgi /var/www/html/wps/
COPY apache2.conf /etc/apache2/
COPY pywps.cfg /etc/
COPY catalog.cfg /home/
COPY docker_configs.py /home/

CMD python /home/docker_configs.py && \
    /etc/init.d/postgresql restart && \
    /etc/init.d/apache2 start && tail -f /dev/null

EXPOSE 80
