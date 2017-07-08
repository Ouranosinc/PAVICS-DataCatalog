import os
import time
import json

from pywps import Process, get_format, configuration
from pywps import LiteralInput, ComplexOutput

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

json_output_path = configuration.get_config_value('server', 'outputpath')
json_format = get_format('JSON')


class GetPoint(Process):
    """
    Please explain what problem this process solves ? Is it used for the web interface (click and return value + metadata) ?
    """
    def __init__(self):
        # From pywps4 code : time_format = '%Y-%m-%dT%H:%M:%S%z'
        # Is that a bug? %z should be %Z
        # Using 'string' data_type until this is corrected.
        inputs = [LiteralInput('opendap_url',
                               'OPeNDAP URL',
                               abstract="An OPeNDAP URL pointing to the netCDF file.",
                               data_type='string',
                               max_occurs=100000),
                  LiteralInput('variable',
                               'Variable name',
                               abstract="Name of the netCDF variable.",
                               data_type='string',
                               max_occurs=1000),
                  LiteralInput('use_ordered_indices',
                               'Use ordered indices',
                               abstract='Whether or not ordered indices are used', # Je ne comprend pas ce que ça veut dire.
                               abstract="",
                               data_type='boolean',
                               default=False,
                               min_occurs=0),
                  LiteralInput('ordered_indice',  # avec un s ? Est-ce qu'on a besoin de use_ordered_indices ?
                               'Ordered indices',
                               abstract='Selected point indices within the netCDF grid.',
                               data_type='integer',
                               default=0,
                               min_occurs=0,
                               max_occurs=10),
                  LiteralInput('named_indice',  # avec un s ?
                               'Named indices',
                               abstract='Indices for the point in the NetCDF variable' \
                               ' with named dimensions (dim:indice)', # Je ne comprend pas
                               data_type='string',
                               default='',
                               min_occurs=0,
                               max_occurs=10),
                  LiteralInput('nearest_to',
                               abstract='Nearest value for each dimension in the ' \
                               'NetCDF variable for the point ' \
                               'with named dimensions (dim:value)',
                               data_type='string',
                               default='',
                               min_occurs=0,
                               max_occurs=10),
                  LiteralInput('threshold',
                               'Thresholds for the distance to each nearest ' \
                               'value with named dimensions (dim:threshold)',
                               data_type='string',
                               default='',
                               min_occurs=0,
                               max_occurs=10)]

        outputs = [ComplexOutput('point_result',
                                 'Information for the requested point',
                                 supported_formats=[json_format])]
        outputs[0].as_reference = True

        super(GetPoint, self).__init__(
            self._handler,
            identifier='getpoint',
            title='Point value from a NetCDF file',
            abstract='Return the value of one or multiple variables at specified locations.',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _value_or_default(self, request, input_name):
        if input_name in request.inputs:
            return [request.inputs[input_name][n].data
                    for n in range(len(request.inputs[input_name]))]
            return request.inputs[input_name][0].data
        else:
            # workaround for poor handling of default values
            return [x.default
                    for x in self.inputs if x.identifier == input_name]

    def _dict_from_sep(self,xs,sep=':',convert=None):
        d = {}
        for x in xs:
            decode_x = x.split(sep)
            if convert is None:
                d[decode_x[0]] = sep.join(decode_x[1:])
            else:
                d[decode_x[0]] = convert(sep.join(decode_x[1:]))
        return d

    def _handler(self, request, response):
        f = self._value_or_default
        g = self._dict_from_sep
        opendap_urls = f(request, 'opendap_url')
        var_names = f(request, 'variable')
        use_ordered_indices = f(request, 'use_ordered_indices')[0]
        if not use_ordered_indices:
            ordered_indices = None
        else:
            ordered_indices = map(int, f(request, 'ordered_indice'))
        named_indices = f(request, 'named_indice')
        if (len(named_indices) == 1) and (not named_indices[0]): #?
            named_indices = None
        else:
            named_indices = g(named_indices, convert=int)
        nearest_to = f(request, 'nearest_to')
        if (len(nearest_to) == 1) and (not nearest_to[0]):
            nearest_to = None
        else:
            d = {}
            for x in nearest_to:
                decode_x = x.split(':')
                try:
                    d[decode_x[0]] = float(':'.join(decode_x[1:]))
                except ValueError:
                    d[decode_x[0]] = ':'.join(decode_x[1:])
            nearest_to = d
        thresholds = f(request, 'threshold')
        if (len(thresholds) == 1) and (not thresholds[0]):
            thresholds = None
        else:
            thresholds = g(thresholds, convert=float)

        point_result = nccombo.get_point(opendap_urls, var_names,
                                         ordered_indices, named_indices,
                                         nearest_to, thresholds)

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        output_file_name = "point_result_%s_.json" % (time_str,)
        output_file = os.path.join(json_output_path, output_file_name)
        f1 = open(output_file, 'w')
        f1.write(json.dumps(point_result))
        f1.close()
        response.outputs['point_result'].file = output_file
        response.outputs['point_result'].output_format = json_format
        return response
