import os
import time
from pywps import Process,get_format,configuration
from pywps import ComplexOutput

from pavics import catalog

env_solr_host = os.environ['SOLR_HOST']
env_solr_port = os.environ['SOLR_POST']
env_thredds_host = os.environ['THREDDS_HOST']
env_thredds_port = os.environ['THREDDS_PORT']
if 'OPENSTACK_INTERNAL_IP' in os.environ:
    env_openstack_interal_ip = os.environ['OPENSTACK_INTERNAL_IP']
else:
	env_openstack_interal_ip = os.environ['SOLR_HOST']

# Example usage:
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=pavicrawler

# Current behaviour: values in the NetCDF files take precedence over the
# values in the Solr database. This could be an option as an input...

# The list of metadata to scan should be in a config file, let's input
# it manually for now:
my_facets = ['experiment','frequency','institute','model','project']
# variable, variable_long_name and cf_standard_name, are not necessarily
# in the global attributes, need to come back for this later...

thredds_server = 'http://%s:%s/thredds' % (env_thredds_host,env_thredds_port)
# base_search_URL in the ESGF Search API is now a solr database URL,
# this is provided as the environment variable SOLR_SERVER.
solr_server = "http://%s:%s/solr/birdhouse/" % (env_solr_host,env_solr_port)
# The user under which apache is running must be able to write to that
# directory.
json_output_path = configuration.get_config_value('server','outputpath')

json_format = get_format('JSON')
gmlxml_format = get_format('GML')

# Fix for OpenStack internal/external ip:
# (the internal ip is the environment variable OPENSTACK_INTERNAL_IP)
internal_ip = env_openstack_internal_ip
external_ip = env_solr_host


class PavicsCrawler(Process):
    def __init__(self):
        inputs = []
        outputs = [ComplexOutput('crawler_result',
                                 'PAVICS Crawler Result',
                                 supported_formats=[json_format])]
        outputs[0].as_reference = True

        super(PavicsCrawler,self).__init__(
            self._handler,
            identifier='pavicrawler',
            title='PAVICS Crawler',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self,request,response):
        update_result = catalog.pavicrawler(thredds_server,solr_server,
                                            my_facets,
                                            set_dataset_id=True,
                                            internal_ip=internal_ip,
                                            external_ip=external_ip,
                                            output_internal_ip=True)

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
        output_file_name = "solr_result_%s_.json" % (time_str,)
        output_file = os.path.join(json_output_path,output_file_name)
        f1 = open(output_file,'w')
        f1.write(update_result)
        f1.close()
        response.outputs['crawler_result'].file = output_file
        response.outputs['crawler_result'].output_format = json_format
        return response