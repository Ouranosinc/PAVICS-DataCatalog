# PAVICS-DataCatalog
DataCatalog Web Processing Service for the PAVICS project

Installation (requires docker - https://www.docker.com):

    docker pull pavics/pavics-datacatalog

Configuration:

Provide the Solr and THREDDS host (if localhost, use the ip address since
this is inside a docker container), as well as the exposed WPS host on which
output files will be available, in the catalog.cfg file.

Running the application:

    docker run --name pavics-datacatalog1 -d -v /path/to/local/catalog.cfg:/home/catalog.cfg -p 8009:80 pavics/pavics-datacatalog

The available processes can be obtained at:

    http://localhost:8009/pywps?service=WPS&request=GetCapabilities&version=1.0.0

Development:

Building the docker image:

As a docker container running the wps:

    docker build -t pavics-datacatalog .

The pywps config file (pywps.cfg) is available. However, the outputurl
and outputpath values should not be modified as they are currently
dynamically set in other places.

Configure as above and run the local build:

    docker run --name pavics-datacatalog1 -d -v /path/to/local/catalog.cfg:/home/catalog.cfg -p 8009:80 pavics-datacatalog

A local solr database can be used:

    docker run --name my_solr -d -p 8983:8983 -t pavics/solr

Solr will be located at http://localhost:8983/solr

New processes must be added to the pavics_datacatalog/wps_processes/__init__.py
file.

Tests configuration is done in the configtests.cfg file in the tests directory.
Tests can be run locally in the tests directory with python test_{something}.py
if the dependencies are all installed locally as well. Otherwise, install
as a package and run:

    python setup.py test

Some relevant log files:

    docker exec -it pavics-datacatalog1 /bin/bash
    cat /var/log/apache2/access.log
    cat /var/log/apache2/error.log
    cat /var/log/postgresql/postgresql-9.5-main.log

Sample WPS calls:

Add test docs to Solr index:

    http://localhost:8009/pywps?service=WPS&request=execute&version=1.0.0&identifier=pavicstestdocs&DataInputs=

Crawler:

    http://localhost:8009/pywps?service=WPS&request=execute&version=1.0.0&identifier=pavicrawler&storeExecuteResponse=true&status=true&DataInputs=
