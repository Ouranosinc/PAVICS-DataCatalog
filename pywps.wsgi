#!/usr/bin/env python
import sys
from pywps.app import Service

sys.path.append('/var/www/html/wps')

# Must first import the process, then add it to the application.
from wps_pavicsearch import PavicsSearch
from wps_pavicsupdate import PavicsUpdate
from wps_pavicrawler import PavicsCrawler
from wps_period2indices import Period2Indices

application = Service(processes=[PavicsSearch(),PavicsUpdate(),PavicsCrawler(),
                                 Period2Indices()])
