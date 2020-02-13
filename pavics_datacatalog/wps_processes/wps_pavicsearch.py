import os
import time
import traceback
import json
from pywps import Process, get_format, configuration
from pywps import LiteralInput, ComplexOutput

from pavics import catalog
from pavics_datacatalog.magpie_utils import MagpieService

import logging
import sys

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


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
        self.magpie_host = os.environ.get('MAGPIE_HOST', None)
        self.verify = os.environ.get('VERIFY', True) not in ['false', 'False']
        svc_name = os.environ.get('THREDDS_HOST_MAGPIE_SVC_NAME', '')
        self.magpie_thredds_servers = {
            svc_name: host for svc_name, host in
            zip(map(str.strip, svc_name.split(',')),
                map(str.strip, os.environ.get('THREDDS_HOST', '').split(',')))}
        self.esgf_nodes = os.environ.get('ESGF_NODES', '').split(',')
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
                               default=0,
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
                               mode=None),
                  LiteralInput('esgf',
                               'Include ESGF search',
                               abstract='Whether to also search ESGF nodes.',
                               data_type='boolean',
                               default=False,
                               min_occurs=0,
                               mode=None),
                  LiteralInput('list_type',
                               'The type of file links in the result list',
                               abstract=('Can be opendap_url, fileserver_url, '
                                         'gridftp_url, globus_url, wms_url'),
                               data_type='string',
                               default='opendap_url',
                               min_occurs=0,
                               mode=None)]

        outputs = [ComplexOutput('search_result',
                                 'PAVICS Catalogue Search Result',
                                 abstract='PAVICS Catalogue Search Result',
                                 supported_formats=[json_format,
                                                    gmlxml_format]),
                   ComplexOutput('list_result',
                                 'List of urls of the search result',
                                 abstract='List of urls of the search result.',
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
            logger.info('using facets : {0}'.format(request.inputs['facets'][0].data))
            facets = request.inputs['facets'][0].data
            if facets == 'None':
                facets = None
        else:
            facets = None
        if 'limit' in request.inputs:
            logger.info('using limit : {0}'.format(request.inputs['limit'][0].data))
            limit = request.inputs['limit'][0].data
        else:
            limit = 10
        if 'offset' in request.inputs:
            logger.info('using offset : {0}'.format(request.inputs['offset'][0].data))
            offset = request.inputs['offset'][0].data
        else:
            offset = 0
        search_type = request.inputs['type'][0].data
        output_format = request.inputs['format'][0].data
        # Not sure if the default should actually be forced to None here...
        fields = request.inputs['fields'][0].data
        if 'constraints' in request.inputs:
            logger.info('using constraints : {0}'.format(request.inputs['constraints'][0].data))
            constraints = request.inputs['constraints'][0].data
        else:
            constraints = None
        if 'query' in request.inputs:
            logger.info('using query : {0}'.format(request.inputs['query'][0].data))
            query = request.inputs['query'][0].data
        else:
            query = None
        if 'esgf' in request.inputs:
            logger.info('using esgf : {0}'.format(request.inputs['esgf'][0].data))
            search_esgf = request.inputs['esgf'][0].data
        else:
            search_esgf = False
        if 'list_type' in request.inputs:
            logger.info('using list_type : {0}'.format(request.inputs['list_type'][0].data))
            list_type = request.inputs['list_type'][0].data
        else:
            list_type = 'opendap_url'

        if search_esgf:
            try:
                logger.info('calling pavics_and_esgf_search to {host} and esgf host {esgf} with : '
                            'facets={facets}, offset={offset}, limit={limit}, '
                            'fields={fields}, query={query}, constraints={constraints}, '
                            'search_type={search_type}, output_format={output_format}'.format(
                    host=self.solr_server, esgf=str(self.esgf_nodes),
                    facets=facets, offset=offset,
                    limit=limit, fields=fields, query=query,
                    constraints=constraints, search_type=search_type,
                    output_format=output_format
                ))
                search_result = catalog.pavics_and_esgf_search(
                    [self.solr_server], self.esgf_nodes, facets=facets,
                    offset=offset, limit=limit, fields=fields, query=query,
                    constraints=constraints, search_type=search_type,
                    output_format=output_format)
            except:
                logger.error(traceback.format_exc())
                raise Exception(traceback.format_exc())
        else:
            try:
                logger.info('calling pavicsearch to {host} with : '
                            'facets={facets}, offset={offset}, limit={limit}, '
                            'fields={fields}, query={query}, constraints={constraints}, '
                            'search_type={search_type}, output_format={output_format}'.format(
                    host=self.solr_server, facets=facets, offset=offset,
                    limit=limit, fields=fields, query=query,
                    constraints=constraints, search_type=search_type,
                    output_format=output_format
                ))
                (search_result, search_url) = catalog.pavicsearch(
                    self.solr_server, facets=facets, offset=offset,
                    limit=limit, fields=fields, query=query,
                    constraints=constraints, search_type=search_type,
                    output_format=output_format)
            except:
                logger.error(traceback.format_exc())
                raise Exception(traceback.format_exc())

        # magpie integration
        if self.magpie_host:
            logger.info('Using magpie')
            try:
                try:
                    token = request.http_request.cookies['auth_tkt']
                except KeyError:
                    logger.info('No token, make an anonymous request')
                    token = None
                mag = MagpieService(
                    self.magpie_host, self.magpie_thredds_servers, token, self.verify)
                ndocs = len(search_result['response']['docs'])
                logger.debug("magpie filtering: initial ndocs=%r" % ndocs)
                for i in range(ndocs - 1, -1, -1):
                    doc = search_result['response']['docs'][i]
                    # Skip if ESGF result
                    if doc['source'] == 'ESGF':
                        continue
                    if hasattr(doc['url'], '__iter__'):
                        for doc_url in doc['url']:
                            if not mag.has_view_perm(doc_url):
                                logger.debug("magpie filtering: removing doc_url=%r" % doc_url)
                                search_result['response']['docs'].pop(i)
                                break
                    else:
                        if not mag.has_view_perm(doc['url']):
                            logger.debug("magpie filtering: removing doc_url=%r" % doc['url'])
                            search_result['response']['docs'].pop(i)
                search_result['response']['numFound'] = \
                    len(search_result['response']['docs'])
                logger.info('Magpie filtering has removed {0} documents'.format(
                    ndocs - len(search_result['response']['docs'])))
            except:
                logger.error('Exception thrown while filtering with magpie')
                logger.error(traceback.format_exc())
                raise Exception(traceback.format_exc())

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        output_file_name = "solr_result_{0}_.".format(time_str)
        if output_format == 'application/solr+json':
            logger.info('Output format is json')
            output_file_name += 'json'
        elif output_format == 'application/solr+xml':
            logger.info('Output format is xml')
            output_file_name += 'xml'
        else:
            # Unsupported format
            logger.info('Unsupported output format')
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
                catalog.list_of_files_from_pavicsearch(search_result,
                                                       list_type)))
        f1.close()

        response.outputs['search_result'].file = output_file
        if output_format == 'application/solr+json':
            response.outputs['search_result'].output_format = json_format
        elif output_format == 'application/solr+xml':
            response.outputs['search_result'].output_format = gmlxml_format
        response.outputs['list_result'].file = output_list_file
        response.outputs['list_result'].output_format = json_format
        logger.info('Search is completed')
        return response
