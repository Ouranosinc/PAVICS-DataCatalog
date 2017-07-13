import os
import time
import traceback
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

# The user under which apache is running must be able to write to that
# directory.
output_path = configuration.get_config_value('server', 'outputpath')

json_format = get_format('JSON')
gmlxml_format = get_format('GML')
text_format = get_format('TEXT')


class PavicsCrawler(Process):
    def __init__(self):
        env_solr_host = os.environ.get('SOLR_HOST', None)
        env_thredds_host = os.environ.get('THREDDS_HOST', '')
        # OPENSTACK support is obsolete
        env_openstack_internal_ip = os.environ.get(
            'OPENSTACK_INTERNAL_IP', os.environ.get('SOLR_HOST', None))
        self.wms_alternate_server = os.environ.get(
            'WMS_ALTERNATE_SERVER', None)
        self.thredds_hosts = map(str.strip, env_thredds_host.split(','))
        self.thredds_servers = []
        for thredds_host in self.thredds_hosts:
            self.thredds_servers.append(
                'http://{0}/thredds'.format(thredds_host))
        # base_search_URL in the ESGF Search API is now a solr database URL,
        # this is provided as the environment variable SOLR_SERVER.
        self.solr_server = "http://{0}/solr/birdhouse/".format(env_solr_host)
        # Fix for OpenStack internal/external ip:
        # (the internal ip is the environment variable OPENSTACK_INTERNAL_IP)
        self.internal_ip = env_openstack_internal_ip
        self.external_ip = env_solr_host

        inputs = [LiteralInput('target_files',
                               'Files to crawl',
                               data_type='string',
                               min_occurs=0,
                               max_occurs=10000),
                  LiteralInput('target_thredds',
                               'Thredds server to scan',
                               data_type='string',
                               min_occurs=0)]
        outputs = [ComplexOutput('crawler_result',
                                 'PAVICS Crawler Result',
                                 supported_formats=[json_format],
                                 as_reference=True)]

        super(PavicsCrawler, self).__init__(
            self._handler,
            identifier='pavicrawler',
            title='PAVICS Crawler',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self, request, response):
        if 'target_files' in request.inputs:
            target_files = []
            for i in range(len(request.inputs['target_files'])):
                target_files.append(request.inputs['target_files'][i].data)
        else:
            target_files = None

        # If a target thredds server is specified, it must be in the list
        # of thredds servers from the config, otherwise we fall back to
        # scanning all thredds servers.
        # Suggestion: decompose the target_thredds and compare individual
        # sections of the url/port to allow more flexibility in the
        # comparison.
        if ('target_thredds' in request.inputs) and \
           (request.inputs['target_thredds'][0].data in self.thredds_servers):
            target_thredds_servers = ["http://{0}/thredds".format(
                request.inputs['target_thredds'][0].data)]
        else:
            target_thredds_servers = self.thredds_servers

        try:
            for thredds_server in target_thredds_servers:
                if '<HOST>' in self.wms_alternate_server:
                    i = self.thredds_servers.index(thredds_server)
                    wms_with_host = self.wms_alternate_server.replace(
                        '<HOST>', self.thredds_hosts[i].split(':')[0])
                else:
                    wms_with_host = self.wms_alternate_server
                update_result = catalog.pavicrawler(
                    thredds_server, self.solr_server, my_facets,
                    set_dataset_id=True, internal_ip=self.internal_ip,
                    external_ip=self.external_ip, output_internal_ip=True,
                    wms_alternate_server=wms_with_host,
                    target_files=target_files)
        except:
            raise Exception(traceback.format_exc())

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        output_file_name = "solr_result_{0}_.json".format(time_str)
        output_file = os.path.join(output_path, output_file_name)
        f1 = open(output_file, 'w')
        f1.write(update_result)
        f1.close()
        response.outputs['crawler_result'].file = output_file
        response.outputs['crawler_result'].output_format = json_format
        return response
