from pywps import Process
from pywps import LiteralInput,LiteralOutput

from pavics import netcdf as pavnc

# Example usage:
#
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=period2indices&DataInputs=initial_date=1962-02-03T00:00:00;\
# final_date=1962-03-31T23:59:59;\
# opendap_url=http://132.217.140.45:8083/thredds/dodsC/birdhouse/ouranos/\
# subdaily/aev/shum/aev_shum_1962.nc


class Period2Indices(Process):
    def __init__(self):
        # From pywps4 code : time_format = '%Y-%m-%dT%H:%M:%S%z'
        # Is that a bug? %z should be %Z
        # Using 'string' data_type until this is corrected.
        cal_abs = 'If left unspecified, taken from NetCDF file time variable.'
        inputs = [LiteralInput('initial_date',
                               'Initial date of the period',
                               data_type='string',
                               abstract='Format must be %Y-%m-%dT%H:%M:%S'),
                  LiteralInput('final_date',
                               'Final date of the period',
                               data_type='string',
                               abstract='Format must be %Y-%m-%dT%H:%M:%S'),
                  LiteralInput('opendap_url',
                               'OPeNDAP url to a NetCDF file',
                               data_type='string'),
                  LiteralInput('calendar',
                               'NetCDF calendar type',
                               data_type='string',
                               abstract=cal_abs,
                               default='gregorian',
                               min_occurs=0),]
        title_ini = 'Initial time index of the period in the NetCDF file'
        title_fin = 'Final time index of the period in the NetCDF file'
        outputs = [LiteralOutput('initial_index',title_ini,
                                 data_type='integer'),
                   LiteralOutput('final_index',title_fin,
                                 data_type='integer',
                                 abstract='The final index is inclusive.'),]

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

    def _handler(self,request,response):
        d = pavnc.period2indices(request.inputs['initial_date'][0].data,
                                 request.inputs['final_date'][0].data,
                                 request.inputs['opendap_url'][0].data,
                                 calendar=request.inputs['calendar'][0].data)
        response.outputs['initial_index'].data = d['initial_index']
        response.outputs['final_index'].data = d['final_index']
        return response
