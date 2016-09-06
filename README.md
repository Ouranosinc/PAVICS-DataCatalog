# PAVICS-DataCatalog
DataCatalog server for the PAVICS project

Installation:

    docker build -t pavicswps .

Running the application:

    docker run --name my_pavicswps -d -p 8080:8080 pavicswps

To access the WPS processes, get the IP address of the container:

    docker inspect my_pavicswps

The available processes can be obtained at:

    http://x.x.x.x/pywps?service=WPS&request=GetCapabilities&version=1.0.0

Currently, this is linked to branch pav133 of the PAVICS project. Also,
a patch is applied to pywps4 to fix a bug described at:

    https://github.com/geopython/pywps/issues/154
