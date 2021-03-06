import os
import time
import json
import traceback
from pywps import Process, get_format, configuration
from pywps import LiteralInput, ComplexOutput

from pavics import catalog

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

# The user under which apache is running must be able to write to that
# directory.
json_output_path = configuration.get_config_value('server', 'outputpath')

json_format = get_format('JSON')
gmlxml_format = get_format('GML')


class PavicsValidate(Process):
    def __init__(self):
        self.solr_server = os.environ.get('SOLR_HOST', None)
        inputs = [LiteralInput('facets',
                               'Required facets',
                               abstract=('Facets that are required to be '
                                         'present in each database entry.'),
                               data_type='string'),
                  LiteralInput('paths',
                               'Search paths',
                               abstract=('Limit validation to certain paths '
                                         'relative to thredds main '
                                         'directory.'),
                               data_type='string',
                               default='',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('files',
                               'Search files',
                               abstract=('Limit validation according to file '
                                         'names.'),
                               data_type='string',
                               default='',
                               min_occurs=0,
                               mode=None)]
        outputs = [ComplexOutput('validation_result',
                                 'Validation result',
                                 abstract='Validation result as a json.',
                                 supported_formats=[json_format])]
        outputs[0].as_reference = True

        super(PavicsValidate, self).__init__(
            self._handler,
            identifier='pavicsvalidate',
            title='PAVICS Catalogue Validation',
            abstract='Query database entries for missing required facets.',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self, request, response):
        facets = request.inputs['facets'][0].data
        facets = facets.split(',')
        if 'paths' in request.inputs:
            paths = request.inputs['paths'][0].data
        else:
            # workaround for poor handling of default values
            paths = None
        if paths:
            paths = paths.split(',')
        if 'files' in request.inputs:
            files = request.inputs['files'][0].data
        else:
            # workaround for poor handling of default values
            paths = None
        if files:
            files = files.split(',')

        try:
            validate_result = catalog.pavicsvalidate(
                self.solr_server, facets, paths, files)
            validate_result = json.dumps(validate_result)
        except:
            raise Exception(traceback.format_exc())

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        output_file_name = "json_result_{0}_.json".format(time_str)
        output_file = os.path.join(json_output_path, output_file_name)
        f1 = open(output_file, 'w')
        f1.write(validate_result)
        f1.close()
        response.outputs['validation_result'].file = output_file
        response.outputs['validation_result'].output_format = json_format
        return response
