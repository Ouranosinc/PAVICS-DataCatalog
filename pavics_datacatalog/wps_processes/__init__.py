from .wps_getpoint import GetPoint
from .wps_ncplotly import NCPlotly
from .wps_pavicrawler import PavicsCrawler
from .wps_pavicsearch import PavicsSearch
from .wps_pavicsupdate import PavicsUpdate
from .wps_pavicsvalidate import PavicsValidate
from .wps_period2indices import Period2Indices
from .wps_test_docs import PavicsTestDocs

processes = [
    GetPoint(),
    NCPlotly(),
    PavicsCrawler(),
    PavicsSearch(),
    PavicsUpdate(),
    PavicsValidate(),
    Period2Indices(),
    PavicsTestDocs(),
]
