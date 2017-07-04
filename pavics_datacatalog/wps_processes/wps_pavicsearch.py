import os
import time
from pywps import Process,get_format,configuration
from pywps import LiteralInput,ComplexOutput

from pavics import catalog

env_solr_host = os.environ.get('SOLR_HOST', None)

# Example usage:
#
# List facets values:
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=pavicsearch&DataInputs=facets=*
#
# Search by facet:
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=pavicsearch&DataInputs=constraints=model:CRCM4,experiment:rcp85

# base_search_URL in the ESGF Search API is now a solr database URL,
# this is provided as the environment variable SOLR_SERVER.
solr_server = "http://%s/solr/birdhouse/" % (env_solr_host,)
# The user under which apache is running must be able to write to that
# directory.
json_output_path = configuration.get_config_value('server','outputpath')

json_format = get_format('JSON')
gmlxml_format = get_format('GML')


class PavicsSearch(Process):
    def __init__(self):
        inputs = [LiteralInput('facets',
                               'Facet values and counts',
                               data_type='string',
                               default='',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('shards',
                               'Shards to be queried',
                               data_type='string',
                               default='*',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('offset',
                               'Pagination offset',
                               data_type='integer',
                               default=0,
                               min_occurs=0,
                               mode=None),
                  LiteralInput('limit',
                               'Pagination limit',
                               data_type='integer',
                               default=10,
                               min_occurs=0,
                               mode=None),
                  LiteralInput('fields',
                               'Metadata fields to return',
                               data_type='string',
                               default='*',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('format',
                               'Output Format',
                               data_type='string',
                               default='application/solr+json',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('query',
                               'Free text search',
                               data_type='string',
                               default='*',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('distrib',
                               'Distributed query',
                               data_type='boolean',
                               default=False,
                               min_occurs=0,
                               mode=None),
                  LiteralInput('type',
                               'Type of the record',
                               data_type='string',
                               default='Dataset',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('constraints',
                               'Search constraints',
                               data_type='string',
                               default='',
                               min_occurs=0,
                               mode=None),]

        outputs = [ComplexOutput('search_result',
                                 'PAVICS Catalogue Search Result',
                                 supported_formats=[json_format,
                                                    gmlxml_format])]
        outputs[0].as_reference = True

        super(PavicsSearch,self).__init__(
            self._handler,
            identifier='pavicsearch',
            title='PAVICS Catalogue Search',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self,request,response):
        if 'facets' in request.inputs:
            facets = request.inputs['facets'][0].data
        else:
            # workaround for poor handling of default values
            facets = None
        if 'limit' in request.inputs:
            limit = request.inputs['limit'][0].data
        else:
            # workaround for poor handling of default values
            for one_input in self.inputs:
                if one_input.identifier == 'limit':
                    limit = one_input.default
        if 'offset' in request.inputs:
            offset = request.inputs['offset'][0].data
        else:
            # workaround for poor handling of default values
            for one_input in self.inputs:
                if one_input.identifier == 'offset':
                    offset = one_input.default
        if 'type' in request.inputs:
            search_type = request.inputs['type'][0].data
        else:
            # workaround for poor handling of default values
            for one_input in self.inputs:
                if one_input.identifier == 'type':
                    search_type = one_input.default
        if 'format' in request.inputs:
            output_format = request.inputs['format'][0].data
        else:
            # workaround for poor handling of default values
            for one_input in self.inputs:
                if one_input.identifier == 'format':
                    output_format = one_input.default
        if 'fields' in request.inputs:
            fields = request.inputs['fields'][0].data
        else:
            # workaround for poor handling of default values
            fields = None
        if 'constraints' in request.inputs:
            constraints = request.inputs['constraints'][0].data
        else:
            # workaround for poor handling of default values
            constraints = None
        if 'query' in request.inputs:
            query = request.inputs['query'][0].data
        else:
            # workaround for poor handling of default values
            query = None

        search_result = catalog.pavicsearch(solr_server,facets,limit,offset,
                                            search_type,output_format,fields,
                                            constraints,query)

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
        output_file_name = "solr_result_%s_." % (time_str,)
        if output_format == 'application/solr+json':
            output_file_name += 'json'
        elif output_format == 'application/solr+xml':
            output_file_name += 'xml'
        else:
            # Unsupported format
            raise NotImplementedError()
        output_file = os.path.join(json_output_path,output_file_name)
        f1 = open(output_file,'w')
        f1.write(search_result)
        f1.close()
        response.outputs['search_result'].file = output_file
        if output_format == 'application/solr+json':
            response.outputs['search_result'].output_format = json_format
        elif output_format == 'application/solr+xml':
            response.outputs['search_result'].output_format = gmlxml_format
        return response
