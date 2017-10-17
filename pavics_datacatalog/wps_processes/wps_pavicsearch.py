import os
import time
import traceback
import json
from pywps import Process, get_format, configuration
from pywps import LiteralInput, ComplexOutput

from pavics import catalog

# Example usage:
#
# List facets values:
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=pavicsearch&DataInputs=facets=*
#
# Search by facet:
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=pavicsearch&DataInputs=constraints=model:CRCM4,experiment:rcp85

# The user under which apache is running must be able to write to that
# directory.
json_output_path = configuration.get_config_value('server', 'outputpath')

json_format = get_format('JSON')
gmlxml_format = get_format('GML')


class PavicsSearch(Process):
    def __init__(self):
        self.solr_server = os.environ.get('SOLR_HOST', None)
        inputs = [LiteralInput('facets',
                               'Facet values and counts',
                               abstract=('Comma separated list of facets; '
                                         'facets are searchable indexing '
                                         'terms in the database.'),
                               data_type='string',
                               default='',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('shards',
                               'Shards to be queried',
                               abstract='Shards to be queried',
                               data_type='string',
                               default='*',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('offset',
                               'Pagination offset',
                               abstract=('Where to start in the document '
                                         'count of the database search.'),
                               data_type='integer',
                               default=0,
                               min_occurs=0,
                               mode=None),
                  LiteralInput('limit',
                               'Pagination limit',
                               abstract=('Maximum number of documents to '
                                         'return.'),
                               data_type='integer',
                               default=10,
                               min_occurs=0,
                               mode=None),
                  LiteralInput('fields',
                               'Metadata fields to return',
                               abstract=('Comme separated list of fields to '
                                         'return.'),
                               data_type='string',
                               default='*',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('format',
                               'Output Format',
                               abstract='Output format.',
                               data_type='string',
                               default='application/solr+json',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('query',
                               'Free text search',
                               abstract='Direct query to the database.',
                               data_type='string',
                               default='*',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('distrib',
                               'Distributed query',
                               abstract='Distributed query',
                               data_type='boolean',
                               default=False,
                               min_occurs=0,
                               mode=None),
                  LiteralInput('type',
                               'Type of the record',
                               abstract=('One of Dataset, File, Aggregate or '
                                         'FileAsAggregate.'),
                               data_type='string',
                               default='Dataset',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('constraints',
                               'Search constraints',
                               abstract=('Format is '
                                         'facet1:value1,facet2:value2,...'),
                               data_type='string',
                               default='',
                               min_occurs=0,
                               mode=None)]

        outputs = [ComplexOutput('search_result',
                                 'PAVICS Catalogue Search Result',
                                 abstract='PAVICS Catalogue Search Result',
                                 supported_formats=[json_format,
                                                    gmlxml_format]),
                   ComplexOutput('list_result',
                                 'List of OPEnDAP urls of the search result',
                                 abstract=('List of OPEnDAP urls of the '
                                           'search result.'),
                                 supported_formats=[json_format])]
        # as_reference now an argument in recent pywps versions?
        outputs[0].as_reference = True
        outputs[1].as_reference = True

        super(PavicsSearch, self).__init__(
            self._handler,
            identifier='pavicsearch',
            title='PAVICS Catalogue Search',
            abstract=('Search the PAVICS database and return a catalogue of '
                      'matches.'),
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self, request, response):
        # So confused about pywps handling of default values...
        # maybe not testing on the proper pywps branch...
        if 'facets' in request.inputs:
            facets = request.inputs['facets'][0].data
        else:
            facets = None
        if 'limit' in request.inputs:
            limit = request.inputs['limit'][0].data
        else:
            limit = 10
        if 'offset' in request.inputs:
            offset = request.inputs['offset'][0].data
        else:
            offset = 0
        search_type = request.inputs['type'][0].data
        output_format = request.inputs['format'][0].data
        # Not sure if the default should actually be forced to None here...
        fields = request.inputs['fields'][0].data
        if 'constraints' in request.inputs:
            constraints = request.inputs['constraints'][0].data
        else:
            constraints = None
        if 'query' in request.inputs:
            query = request.inputs['query'][0].data
        else:
            query = None

        try:
            search_result = catalog.pavicsearch(
                self.solr_server, facets, limit, offset, search_type,
                output_format, fields, constraints, query)
        except:
            raise Exception(traceback.format_exc())

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        output_file_name = "solr_result_{0}_.".format(time_str)
        if output_format == 'application/solr+json':
            output_file_name += 'json'
        elif output_format == 'application/solr+xml':
            output_file_name += 'xml'
        else:
            # Unsupported format
            raise NotImplementedError()
        list_file_name = "list_result_{0}_.json".format(time_str)

        output_file = os.path.join(json_output_path, output_file_name)
        f1 = open(output_file, 'w')
        f1.write(json.dumps(search_result))
        f1.close()
        output_list_file = os.path.join(json_output_path, list_file_name)
        f1 = open(output_list_file, 'w')
        if search_type == 'Dataset':
            f1.write("[]")
        else:
            f1.write(json.dumps(
                catalog.list_of_files_from_pavicsearch(search_result)))
        f1.close()

        response.outputs['search_result'].file = output_file
        if output_format == 'application/solr+json':
            response.outputs['search_result'].output_format = json_format
        elif output_format == 'application/solr+xml':
            response.outputs['search_result'].output_format = gmlxml_format
        response.outputs['list_result'].file = output_list_file
        response.outputs['list_result'].output_format = json_format
        return response
