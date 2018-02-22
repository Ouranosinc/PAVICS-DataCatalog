import os
import time
import json
import traceback
from pywps import Process, get_format, configuration
from pywps import ComplexOutput

from pavics import catalog

# Example usage:
# http://localhost:8009/pywps?service=WPS&request=execute&version=1.0.0&identifier=pavicstestdocs&DataInputs=

output_path = configuration.get_config_value('server', 'outputpath')

json_format = get_format('JSON')


class PavicsTestDocs(Process):
    def __init__(self):
        self.solr_server = os.environ.get('SOLR_HOST', None)
        inputs = []
        outputs = [ComplexOutput('solr_result',
                                 title='Solr result',
                                 supported_formats=[json_format],
                                 abstract='Solr result as a json.',
                                 as_reference=True)]

        super(PavicsTestDocs, self).__init__(
            self._handler,
            identifier='pavicstestdocs',
            title='PAVICS Catalog test documents',
            abstract='Add test documents to Solr index.',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=False,
            status_supported=False)

    def _handler(self, request, response):
        docs = [
            {'catalog_url': 'https://localhost/thredds/catalog/birdhouse/PavicsTestDocs.01',
             'category': 'thredds',
             'cf_standard_name': ['test_variable'],
             'content_type': 'application/netcdf',
             'dataset_id': 'PavicsTestDocs-01',
             'datetime_max': '2016-12-31T23:59:59Z',
             'datetime_min': '2016-01-01T00:00:00Z',
             'fileserver_url': 'https://localhost/thredds/fileServer/birdhouse/PavicsTestDocs.01',
             'last_modified': '2018-01-01T00:00:00Z',
             'latest': True,
             'opendap_url': 'https://localhost/thredds/dodsC/birdhouse/PavicsTestDocs.01',
             'project': 'PavicsTestDocs',
             'replica': False,
             'resourcename': 'birdhouse/PavicsTestDocs.01',
             'source': 'https://localhost/thredds/catalog.xml',
             'subject': 'Birdhouse Thredds Catalog',
             'title': 'PavicsTestDocs.01',
             'type': 'File',
             'units': ['1'],
             'url': 'https://localhost/thredds/fileServer/birdhouse/PavicsTestDocs.01',
             'variable': ['test'],
             'variable_long_name': ['Test variable'],
             'wms_url': 'https://localhost/ncWMS2/wms?Dataset=PavicsTestDocs.01',
             },
            {'catalog_url': 'https://localhost/thredds/catalog/birdhouse/PavicsTestDocs.02',
             'category': 'thredds',
             'cf_standard_name': ['test_variable'],
             'content_type': 'application/netcdf',
             'dataset_id': 'PavicsTestDocs-02',
             'datetime_max': '2017-12-31T23:59:59Z',
             'datetime_min': '2017-01-01T00:00:00Z',
             'fileserver_url': 'https://localhost/thredds/fileServer/birdhouse/PavicsTestDocs.02',
             'last_modified': '2018-01-01T00:00:00Z',
             'latest': True,
             'opendap_url': 'https://localhost/thredds/dodsC/birdhouse/PavicsTestDocs.02',
             'project': 'PavicsTestDocs',
             'replica': False,
             'resourcename': 'birdhouse/PavicsTestDocs.02',
             'source': 'https://localhost/thredds/catalog.xml',
             'subject': 'Birdhouse Thredds Catalog',
             'title': 'PavicsTestDocs.02',
             'type': 'File',
             'units': ['1'],
             'url': 'https://localhost/thredds/fileServer/birdhouse/PavicsTestDocs.02',
             'variable': ['test'],
             'variable_long_name': ['Test variable'],
             'wms_url': 'https://localhost/ncWMS2/wms?Dataset=PavicsTestDocs.02',
             },
        ]

        try:
            solr_result = catalog.solr_update(self.solr_server, docs)
        except:
            raise Exception(traceback.format_exc())

        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        output_file_name = "solr_result_{0}.json".format(time_str)
        output_file = os.path.join(output_path, output_file_name)
        with open(output_file, 'w') as f:
            f.write(json.dumps(solr_result))
        response.outputs['solr_result'].file = output_file
        response.outputs['solr_result'].output_format = json_format
        return response
