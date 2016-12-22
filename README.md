# PAVICS-DataCatalog
DataCatalog server for the PAVICS project

Installation:

    docker build -t pavicswps .

Running the application:

    docker run --name my_pavicswps -d -p 8009:80 -e SOLR_HOST=x.x.x.x -e SOLR_PORT=xxxx -e OPENSTACK_INTERNAL_IP=x.x.x.x -e WPS_HOST=x.x.x.x -e WPS_PORT=xxxx -e THREDDS_HOST=x.x.x.x -e THREDDS_PORT=xxxx pavicswps

WPS_HOST and WPS_PORT correspond to the host:port that will be exposed by
this service to store output files.

OPENSTACK_INTERNAL_IP is used to swap internal and external ip in an openstack
context, optional.

The available processes can be obtained at:

    http://localhost:8009/pywps?service=WPS&request=GetCapabilities&version=1.0.0

The PAVICS wps processes that return a json file url use port 8009. This
could be modified to be another input (environment variable) in the future.

The pywps config file (pywps.cfg) is available. However, the outputurl
and outputpath values should not be modified as they are currently
hardcoded in other places.
