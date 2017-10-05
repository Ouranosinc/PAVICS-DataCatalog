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
    def __init__(self):
        # From pywps4 code : time_format = '%Y-%m-%dT%H:%M:%S%z'
        # Is that a bug? %z should be %Z
        # Using 'string' data_type until this is corrected.
        inputs = [
            LiteralInput('opendap_url',
                         'OPeNDAP url to NetCDF file',
                         abstract='OPeNDAP url to NetCDF file.',
                         data_type='string',
                         max_occurs=100000),
            LiteralInput('variable',
                         'NetCDF variable name',
                         abstract='NetCDF variable name.',
                         data_type='string',
                         max_occurs=1000),
            LiteralInput('use_ordered_indices',
                         'Use ordered indices',
                         abstract='Whether ordered indices are used.',
                         data_type='boolean',
                         default=False,
                         min_occurs=0),
            LiteralInput('ordered_index',
                         'Ordered index',
                         abstract=('Indices for the point in the NetCDF '
                                   'variable.'),
                         data_type='integer',
                         default=0,
                         min_occurs=0,
                         max_occurs=10),
            LiteralInput('named_index',
                         'Named index',
                         abstract=('Indices for the point in the NetCDF '
                                   'variable with named dimensions '
                                   '(dim:index).'),
                         data_type='string',
                         default='',
                         min_occurs=0,
                         max_occurs=10),
            LiteralInput('nearest_to',
                         'Nearest to',
                         abstract=('Nearest value for each dimension in the '
                                   'NetCDF variable for the point with named '
                                   'dimensions (dim:value).'),
                         data_type='string',
                         default='',
                         min_occurs=0,
                         max_occurs=10),
            LiteralInput('threshold',
                         'Threshold',
                         abstract=('Thresholds for the distance to each '
                                   'nearest value with named dimensions '
                                   '(dim:threshold).'),
                         data_type='string',
                         default='',
                         min_occurs=0,
                         max_occurs=10)]

        outputs = [ComplexOutput('point_result',
                                 'Information for the requested point',
                                 abstract=('Information for the requested '
                                           'point.'),
                                 supported_formats=[json_format])]
        outputs[0].as_reference = True

        super(GetPoint, self).__init__(
            self._handler,
            identifier='getpoint',
            title='Point value from a NetCDF file',
            abstract='Return a single value from a NetCDF file at the given grid coordinates.',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _dict_from_sep(self, xs, sep=':', convert=None):
        d = {}
        for x in xs:
            decode_x = x.split(sep)
            if convert is None:
                d[decode_x[0]] = sep.join(decode_x[1:])
            else:
                d[decode_x[0]] = convert(sep.join(decode_x[1:]))
        return d

    def _handler(self, request, response):
        opendap_urls = [request.inputs['opendap_url'][n].data
                        for n in range(len(request.inputs['opendap_url']))]

        var_names = [request.inputs['variable'][n].data
                     for n in range(len(request.inputs['variable']))]

        if 'use_ordered_indices' in request.inputs:
            use_ordered_indices = request.inputs['use_ordered_indices'][0].data
        else:
            use_ordered_indices = False

        if not use_ordered_indices:
            ordered_indices = None
        else:
            ndims = len(request.inputs['ordered_index'])
            ordered_indices = [request.inputs['ordered_index'][n].data
                               for n in range(ndims)]

        if 'named_index' in request.inputs:
            ndims = len(request.inputs['named_index'])
            named_indices = [request.inputs['named_index'][n].data
                             for n in range(ndims)]
            named_indices = self._dict_from_sep(named_indices, convert=int)
        else:
            named_indices = None

        if 'nearest_to' in request.inputs:
            nearest_to = [request.inputs['nearest_to'][n].data
                          for n in range(len(request.inputs['nearest_to']))]
            d = {}
            for x in nearest_to:
                decode_x = x.split(':')
                try:
                    d[decode_x[0]] = float(':'.join(decode_x[1:]))
                except ValueError:
                    d[decode_x[0]] = ':'.join(decode_x[1:])
            nearest_to = d
        else:
            nearest_to = None

        if 'thresholds' in request.inputs:
            thresholds = [request.inputs['threshold'][n].data
                          for n in range(len(request.inputs['threshold']))]
            thresholds = self.dict_from_sep(thresholds, convert=float)
        else:
            thresholds = None

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
