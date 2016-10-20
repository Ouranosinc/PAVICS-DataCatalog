#!/usr/bin/env python
import sys
from pywps.app import Service

sys.path.append('/var/www/html/wps')

# Must first import the process, then add it to the application.
from wps_pavicsearch import PavicsSearch
from wps_pavicsupdate import PavicsUpdate
from wps_pavicrawler import PavicsCrawler
from wps_pavicsvalidate import PavicsValidate
from wps_period2indices import Period2Indices
from wps_ncplotly import NCPlotly

application = Service(processes=[PavicsSearch(),PavicsUpdate(),PavicsCrawler(),
                                 PavicsValidate(),Period2Indices(),NCPlotly()])
