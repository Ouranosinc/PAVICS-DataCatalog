#!/usr/bin/env python
import sys
from pywps.app import Service
from pavics_datacatalog import processes

# Must first import the process, then add it to the application.

application = Service(processes=processes)
