import os
import time
import traceback
import json
import requests
from urlparse import urlparse
from pywps import Process, get_format, configuration
from pywps import LiteralInput, ComplexOutput

from pavics import catalog

# Example usage:
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=pavicrawler&storeExecuteResponse=true&status=true&DataInputs=

# Current behaviour: values in the NetCDF files take precedence over the
# values in the Solr database. This could be an option as an input...

# The list of metadata to scan should be in a config file, let's input
# it manually for now:
my_facets = ['experiment', 'frequency', 'institute', 'model', 'project']
# variable, variable_long_name and cf_standard_name, are not necessarily
# in the global attributes, need to come back for this later...

# This list of ignored thredds directories could also be a config...
my_thredds_ignore = ['birdhouse/wps_outputs', 'birdhouse/workspaces']

# The user under which apache is running must be able to write to that
# directory.
output_path = configuration.get_config_value('server', 'outputpath')

json_format = get_format('JSON')
gmlxml_format = get_format('GML')
text_format = get_format('TEXT')


class PavicsCrawler(Process):
    def __init__(self):
        self.solr_server = os.environ.get('SOLR_HOST', None)
        env_thredds_host = os.environ.get('THREDDS_HOST', '')
        self.wms_alternate_server = os.environ.get(
            'WMS_ALTERNATE_SERVER', None)
        self.thredds_servers = map(str.strip, env_thredds_host.split(','))
        self.magpie_host = os.environ.get('MAGPIE_HOST', None)
        self.magpie_credentials = dict(
            provider_name='ziggurat',
            user_name=os.environ.get('MAGPIE_USER', ''),
            password=os.environ.get('MAGPIE_PW', ''))
        self.verify = os.environ.get('VERIFY', True) not in ['false', 'False']
        inputs = [LiteralInput('target_files',
                               'Paths to crawl',
                               abstract=('Only those paths names will be '
                                         'crawled.'),
                               data_type='string',
                               min_occurs=0,
                               max_occurs=10000),
                  LiteralInput('ignored_files',
                               'Paths to ignore during crawling',
                               abstract=('Those paths will be ignored.'),
                               data_type='string',
                               min_occurs=0,
                               max_occurs=10000),
                  LiteralInput('target_thredds',
                               'Thredds server to scan',
                               abstract='Thredds server to scan.',
                               data_type='string',
                               min_occurs=0)]
        outputs = [ComplexOutput('crawler_result',
                                 'PAVICS Crawler Result',
                                 abstract='Crawler result as a json.',
                                 supported_formats=[json_format],
                                 as_reference=True)]

        super(PavicsCrawler, self).__init__(
            self._handler,
            identifier='pavicrawler',
            title='PAVICS Crawler',
            abstract=('Crawl thredds server and write metadata to SOLR '
                      'database.'),
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self, request, response):
        response.update_status('Reading inputs', 1)
        if 'target_files' in request.inputs:
            target_files = [x.data for x in request.inputs['target_files']]
        else:
            target_files = None
        if 'ignored_files' in request.inputs:
            ignored_files = [x.data for x in request.inputs['ignored_files']]
        else:
            ignored_files = my_thredds_ignore

        # If a target thredds server is specified, it must be in the list
        # of thredds servers from the config, otherwise we fall back to
        # scanning all thredds servers.
        # Suggestion: decompose the target_thredds and compare individual
        # sections of the url/port to allow more flexibility in the
        # comparison.
        if ('target_thredds' in request.inputs) and \
           (request.inputs['target_thredds'][0].data in self.thredds_servers):
            target_thredds_servers = [request.inputs['target_thredds'][0].data]
        else:
            target_thredds_servers = self.thredds_servers

        response.update_status('Starting pavicrawler operation', 5)
        try:
            if self.magpie_host:
                response.update_status('Getting magpie authentication', 6)
                s = requests.Session()
                req_response = s.post('{0}/signin'.format(self.magpie_host),
                                      data=self.magpie_credentials,
                                      verify=self.verify)
                auth_tkt = req_response.cookies.get(
                    'auth_tkt', domain=urlparse(self.magpie_host).netloc)
                headers = dict(Cookie='auth_tkt={0}'.format(auth_tkt))
            else:
                headers = None

            response.update_status('Calling pavicrawler', 10)
            for thredds_server in target_thredds_servers:
                if (self.wms_alternate_server is not None) and \
                   ('<HOST>' in self.wms_alternate_server):
                    wms_with_host = self.wms_alternate_server.replace(
                        '<HOST>', thredds_server.split('/')[2].split(':')[0])
                else:
                    wms_with_host = self.wms_alternate_server
                update_result = catalog.pavicrawler(
                    thredds_server, self.solr_server, my_facets,
                    set_dataset_id=True, wms_alternate_server=wms_with_host,
                    target_files=target_files, ignored_files=ignored_files,
                    headers=headers, verify=self.verify)
        except:
            raise Exception(traceback.format_exc())

        response.update_status('Setting outputs', 95)
        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        output_file_name = "solr_result_{0}_.json".format(time_str)
        output_file = os.path.join(output_path, output_file_name)
        f1 = open(output_file, 'w')
        f1.write(json.dumps(update_result))
        f1.close()
        response.outputs['crawler_result'].file = output_file
        response.outputs['crawler_result'].output_format = json_format
        return response
