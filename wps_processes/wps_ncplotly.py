import os
import time
import json
from pywps import Process,get_format,configuration
from pywps import LiteralInput,ComplexOutput

from pavics import ncplotly

# Example usage:
#
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=ncplotly&DataInputs=opendap_url=http://132.217.140.45:8083/\
# thredds/dodsC/birdhouse/ouranos/subdaily/aet/pcp/aet_pcp_1970.nc;\
# variable_name=PCP;time_initial_indice=124;time_final_indice=360;\
# spatial1_initial_indice=100;spatial1_final_indice=101;\
# spatial2_initial_indice=130;spatial2_final_indice=131

# The user under which apache is running must be able to write to that
# directory.
json_output_path = configuration.get_config_value('server','outputpath')

json_format = get_format('JSON')


class NCPlotly(Process):
    def __init__(self):
        # Should specify whether indices are inclusive or exclusive.
        inputs = [LiteralInput('opendap_url',
                               'OPeNDAP url to a NetCDF file',
                               data_type='string'),
                  LiteralInput('variable_name',
                               'Variable name in the NetCDF file',
                               data_type='string'),
                  LiteralInput('time_initial_indice',
                               'Initial indice for time dimension',
                               data_type='integer',
                               min_occurs=0),
                  LiteralInput('time_final_indice',
                               'Final indice for time dimension',
                               data_type='integer',
                               min_occurs=0),
                  LiteralInput('level_initial_indice',
                               'Initial indice for level dimension',
                               data_type='integer',
                               min_occurs=0),
                  LiteralInput('level_final_indice',
                               'Final indice for level dimension',
                               data_type='integer',
                               min_occurs=0),
                  LiteralInput('spatial1_initial_indice',
                               'Initial indice for first spatial dimension',
                               data_type='integer',
                               min_occurs=0),
                  LiteralInput('spatial1_final_indice',
                               'Final indice for first spatial dimension',
                               data_type='integer',
                               min_occurs=0),
                  LiteralInput('spatial2_initial_indice',
                               'Initial indice for second spatial dimension',
                               data_type='integer',
                               min_occurs=0),
                  LiteralInput('spatial2_final_indice',
                               'Final indice for second spatial dimension',
                               data_type='integer',
                               min_occurs=0),]

        outputs = [ComplexOutput('plotly_result',
                                 'Plotly result',
                                 supported_formats=[json_format])]
        outputs[0].as_reference = True

        super(NCPlotly,self).__init__(
            self._handler,
            identifier='ncplotly',
            title='NetCDF plotly',
            abstract='Obtain a plotly object.',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self,request,response):
        d = ncplotly.ncplotly_from_slice(
            request.inputs['opendap_url'][0].data,
            request.inputs['variable_name'][0].data,
            request.inputs['time_initial_indice'][0].data,
            request.inputs['time_final_indice'][0].data,
            request.inputs['level_initial_indice'][0].data,
            request.inputs['level_final_indice'][0].data,
            request.inputs['spatial1_initial_indice'][0].data,
            request.inputs['spatial1_final_indice'][0].data,
            request.inputs['spatial2_initial_indice'][0].data,
            request.inputs['spatial2_final_indice'][0].data)
        plotly_result = json.dumps(d)

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
        output_file_name = "plotly_result_%s_.json" % (time_str,)
        output_file = os.path.join(json_output_path,output_file_name)
        f1 = open(output_file,'w')
        f1.write(plotly_result)
        f1.close()
        response.outputs['plotly_result'].file = output_file
        response.outputs['plotly_result'].output_format = json_format
        return response
