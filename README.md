# PAVICS-DataCatalog
DataCatalog server for the PAVICS project

Installation:

    docker build -t pavicswps .

Running the application:

    docker run --name my_pavicswps -d -p 8009:80 -e SOLR_SERVER=x.x.x.x -e OPENSTACK_INTERNAL_IP=x.x.x.x pavicswps

The available processes can be obtained at:

    http://localhost:8009/pywps?service=WPS&request=GetCapabilities&version=1.0.0

Currently, this is linked to branch pav133 of the PAVICS project. Also,
we revert back to RC1 of pywps4 (8bcea628d22f36dd50a2b9f49cdd7f1d63aea825)
because of a bug in RC2:

    https://github.com/geopython/pywps/issues/176

and a patch is applied to pywps4 to fix a bug described at:

    https://github.com/geopython/pywps/issues/154
