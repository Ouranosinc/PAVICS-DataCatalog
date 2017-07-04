import os
import time
import traceback
from pywps import Process, get_format, configuration
from pywps import LiteralInput, ComplexOutput

from pavics import catalog

env_solr_host = os.environ.get('SOLR_HOST', None)
env_thredds_host = os.environ.get('THREDDS_HOST', None)
# OPENSTACK support is obsolete
env_openstack_internal_ip = os.environ.get(
    'OPENSTACK_INTERNAL_IP', os.environ.get('SOLR_HOST', None))
wms_alternate_server = os.environ.get('WMS_ALTERNATE_SERVER', None)

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

thredds_servers = []
for thredds_server in env_thredds_host.split(','):
    thredds_servers.append('http://{0}/thredds'.format(thredds_server.strip()))
# base_search_URL in the ESGF Search API is now a solr database URL,
# this is provided as the environment variable SOLR_SERVER.
solr_server = "http://%s/solr/birdhouse/" % (env_solr_host,)
# The user under which apache is running must be able to write to that
# directory.
output_path = configuration.get_config_value('server', 'outputpath')

json_format = get_format('JSON')
gmlxml_format = get_format('GML')
text_format = get_format('TEXT')


# Fix for OpenStack internal/external ip:
# (the internal ip is the environment variable OPENSTACK_INTERNAL_IP)
internal_ip = env_openstack_internal_ip
external_ip = env_solr_host


class PavicsCrawler(Process):
    def __init__(self):
        inputs = [LiteralInput('target_files',
                               'Files to crawl',
                               data_type='string',
                               min_occurs=0,
                               max_occurs=10000)]
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
        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        if 'target_files' in request.inputs:
            target_files = []
            for i in range(len(request.inputs['target_files'])):
                target_files.append(request.inputs['target_files'][i].data)
        else:
            target_files = None

        try:
            for thredds_server in thredds_servers:
                update_result = catalog.pavicrawler(
                    thredds_server, solr_server, my_facets,
                    set_dataset_id=True, internal_ip=internal_ip,
                    external_ip=external_ip, output_internal_ip=True,
                    wms_alternate_server=wms_alternate_server,
                    target_files=target_files)
        except:
            raise Exception(traceback.format_exc())

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        output_file_name = "solr_result_%s_.json" % (time_str,)
        output_file = os.path.join(output_path, output_file_name)
        f1 = open(output_file, 'w')
        f1.write(update_result)
        f1.close()
        response.outputs['crawler_result'].file = output_file
        response.outputs['crawler_result'].output_format = json_format
        return response
