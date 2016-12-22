import os
import time
from pywps import Process,get_format,configuration
from pywps import LiteralInput,ComplexOutput

from pavics import catalog

env_solr_host = os.environ['SOLR_HOST']
env_solr_port = os.environ['SOLR_POST']

# Example usage:
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=pavicsupdate&DataInputs=source=source_string;url=url_string;\
# updates=subject:new_subject,units:m

# Still need to perhaps validate the inputs, and consider whether we want
# to do updates that involve list of entries (not tested yet)

# base_search_URL in the ESGF Search API is now a solr database URL,
# this is provided as the environment variable SOLR_SERVER.
solr_server = "http://%s:%s/solr/birdhouse/" % (env_solr_host,env_solr_port)
# The user under which apache is running must be able to write to that
# directory.
json_output_path = configuration.get_config_value('server','outputpath')

json_format = get_format('JSON')
gmlxml_format = get_format('GML')


class PavicsUpdate(Process):
    def __init__(self):
        # The combination of the 'source' and 'url' fields provide the 'id'
        # in the Solr database, they both must be provided.
        inputs = [LiteralInput('id',
                               'id field of the dataset or file',
                               data_type='string'),
                  LiteralInput('type',
                               'Dataset or File',
                               data_type='string',
                               default='File',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('updates',
                               'Fields to update with their new values',
                               data_type='string'),]
        outputs = [ComplexOutput('update_result',
                                 'PAVICS Catalogue Update Result',
                                 supported_formats=[json_format])]
        outputs[0].as_reference = True

        super(PavicsUpdate,self).__init__(
            self._handler,
            identifier='pavicsupdate',
            title='PAVICS Catalogue Update',
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self,request,response):
        # Get the source and url to setup the update dictionary.
        update_id = request.inputs['id'][0].data
        update_type = request.inputs['type'][0].data
        if update_type is None:
            update_type = request.inputs['type'][0].default
        if update_type == 'File':
            update_dict = {'id':update_id}
        elif update_type == 'Dataset':
            update_dict = {'dataset_id':update_id}
        else:
            raise NotImplementedError()
        # Get updates, which are the facets to add/modify.
        data_inputs = request.inputs['updates'][0].data
        # Split using comma & colon as separator
        key_value_pairs = data_inputs.split(',')
        for key_value_pair in key_value_pairs:
            kv = key_value_pair.split(':')
            # Here, we do not use the {'set':kv[1]} syntax, it does not work
            # in birdhouse-solr. Instead it's like adding a new entry, but
            # since the source and url already exist, it will update the other
            # fields.
            update_dict.update({kv[0]:kv[1]})

        update_result = catalog.pavicsupdate(solr_server,update_dict)

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
        output_file_name = "solr_result_%s_.json" % (time_str,)
        output_file = os.path.join(json_output_path,output_file_name)
        f1 = open(output_file,'w')
        f1.write(update_result)
        f1.close()
        response.outputs['update_result'].file = output_file
        response.outputs['update_result'].output_format = json_format
        return response
