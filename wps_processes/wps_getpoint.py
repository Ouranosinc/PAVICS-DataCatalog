import json

from pywps import Process,get_format,configuration
from pywps import LiteralInput,LiteralOutput

from pavics import nccombo

# Example usage:
#
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=getpoint&DataInputs=\
# opendap_url=http://132.217.140.45:8083/thredds/dodsC/birdhouse/ouranos/\
# subdaily/aev/shum/aev_shum_1962.nc;\
# opendap_url=http://132.217.140.45:8083/thredds/dodsC/birdhouse/ouranos/\
# subdaily/aev/shum/aev_shum_1963.nc;variable=SHUM;ordered_indice=0;\
# ordered_indice=0,ordered_indice=70,ordered_indice=30

json_output_path = configuration.get_config_value('server','outputpath')
json_format = get_format('JSON')

class GetPoint(Process):
    def __init__(self):
        # From pywps4 code : time_format = '%Y-%m-%dT%H:%M:%S%z'
        # Is that a bug? %z should be %Z
        # Using 'string' data_type until this is corrected.
        cal_abs = 'If left unspecified, taken from NetCDF file time variable.'
        inputs = [LiteralInput('opendap_url',
                               'OPeNDAP url to a NetCDF file',
                               data_type='string'),
                  LiteralInput('variable',
                               'NetCDF variable name',
                               data_type='string'),
                  LiteralInput('ordered_indice',
                               'Indices for the point in the NetCDF variable',
                               data_type='int',
                               default='',
                               min_occurs=0),
                  LiteralInput('named_indice',
                               'Indices for the point in the NetCDF variable' \
                               ' with named dimensions (dim:indice)',
                               data_type='string',
                               default='',
                               min_occurs=0),
                  LiteralInput('nearest_to',
                               'Nearest value for each dimension in the ' \
                               'NetCDF variable for the point ' \
                               'with named dimensions (dim:value)',
                               data_type='string',
                               default='',
                               min_occurs=0),
                  LiteralInput('threshold',
                               'Threshold for the distance to each nearest ' \
                               'value with named dimensions (dim:threshold)',
                               data_type='string',
                               default='',
                               min_occurs=0),]

        outputs = [ComplexOutput('point_result',
                                 'Information for the requested point',
                                 supported_formats=[json_format])]
        outputs[0].as_reference = True

        super(Period2Indices,self).__init__(
            self._handler,
            identifier='period2indices',
            title='NetCDF time indices from a period',
            abstract='The final index is inclusive.',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _value_or_default(self,request,input_name):
        if input_name in request.inputs:
            return request.inputs[intput_name][0].data
        else:
            # workaround for poor handling of default values
            return [x.default
                    for x in self.intputs if x.identifier == input_name][0]

    def _handler(self,request,response):
        calendar = self._value_or_default(request,'calendar')
        
        point_result = nccombo.get_point()
        
        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
        output_file_name = "point_result_%s_.json" % (time_str,)
        output_file = os.path.join(json_output_path,output_file_name)
        f1 = open(output_file,'w')
        f1.write(json.dumps(point_result))
        f1.close()
        response.outputs['point_result'].file = output_file
        response.outputs['point_result'].output_format = json_format
        return response
