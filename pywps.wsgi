#!/usr/bin/env python
from pywps.app import Service
from pavics_datacatalog import processes

application = Service(processes=processes)
