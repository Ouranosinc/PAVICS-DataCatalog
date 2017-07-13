# PAVICS-DataCatalog
DataCatalog server for the PAVICS project

Installation:

As a docker container running the wps:

    docker build -t pavics-datacatalog .

Configuration:

Provide the SOLR and THREDDS host, as well as the exposed WPS host on which
output files will be available in the catalog.cfg file.

Running the application:

    docker run --name pavics-datacatalog1 -d -p 8009:80 pavics-datacatalog

The available processes can be obtained at:

    http://localhost:8009/pywps?service=WPS&request=GetCapabilities&version=1.0.0

The pywps config file (pywps.cfg) is available. However, the outputurl
and outputpath values should not be modified as they are currently
hardcoded in other places.

Development:

New processes must be added to the pavics_datacatalog/wps_processes/__init__.py
file.

Tests configuration is done in the configtests.cfg file in the tests directory.
Tests can be run locally in the tests directory with python test_{something}.py
if the dependencies are all installed locally as well. Otherwise, install
as a package and run:

    python setup.py test
