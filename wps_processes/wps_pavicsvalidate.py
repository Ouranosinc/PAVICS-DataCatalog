import os
import time
import json
from pywps import Process,get_format,configuration
from pywps import LiteralInput,ComplexOutput

from pavics import catalog

env_solr_host = os.environ['SOLR_HOST']
env_solr_port = os.environ['SOLR_POST']

# Example usage:
#
# Check whether certain facets exist for all entries:
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=pavicsvalidate&DataInputs=facets=model,variable
#
# Check whether certain facets exist for particular files:
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=pavicsvalidate&DataInputs=facets=model,variable;\
# paths=sio%2Fsrtm30_plus_v6,ouranos%2Fsubdaily;\
# files=srtm30_plus.nc,aev_shum_1961.nc

# base_search_URL in the ESGF Search API is now a solr database URL,
# this is provided as the environment variable SOLR_SERVER.
solr_server = "http://%s:%s/solr/birdhouse/" % (env_solr_host,env_solr_port)
# The user under which apache is running must be able to write to that
# directory.
json_output_path = configuration.get_config_value('server','outputpath')

json_format = get_format('JSON')
gmlxml_format = get_format('GML')


class PavicsValidate(Process):
    def __init__(self):
        inputs = [LiteralInput('facets',
                               'Required facets',
                               data_type='string'),
                  LiteralInput('paths',
                               'Search paths',
                               data_type='string',
                               default='',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('files',
                               'Search files',
                               data_type='string',
                               default='',
                               min_occurs=0,
                               mode=None),]
        outputs = [ComplexOutput('validation_result',
                                 'Validation result',
                                 supported_formats=[json_format])]
        outputs[0].as_reference = True

        super(PavicsValidate,self).__init__(
            self._handler,
            identifier='pavicsvalidate',
            title='PAVICS Catalogue Validation',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self,request,response):
        facets = request.inputs['facets'][0].data
        facets = facets.split(',')
        paths = request.inputs['paths'][0].data
        if paths is not None:
            paths = paths.split(',')
        files = request.inputs['files'][0].data
        if files is not None:
            files = files.split(',')

        validate_result = catalog.pavicsvalidate(solr_server,facets,
                                                 paths,files)
        validate_result = json.dumps(validate_result)

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
        output_file_name = "json_result_%s_.json" % (time_str,)
        output_file = os.path.join(json_output_path,output_file_name)
        f1 = open(output_file,'w')
        f1.write(validate_result)
        f1.close()
        response.outputs['validation_result'].file = output_file
        response.outputs['validation_result'].output_format = json_format
        return response
