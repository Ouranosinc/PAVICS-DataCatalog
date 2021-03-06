import os
import time
import traceback
import json
from pywps import Process, get_format, configuration
from pywps import LiteralInput, ComplexOutput

from pavics import catalog

# Example usage:
# localhost/pywps?service=WPS&request=execute&version=1.0.0&\
# identifier=pavicsupdate&DataInputs=source=source_string;url=url_string;\
# updates=subject:new_subject,units:m

# Still need to perhaps validate the inputs, and consider whether we want
# to do updates that involve list of entries (not tested yet)

# The user under which apache is running must be able to write to that
# directory.
json_output_path = configuration.get_config_value('server', 'outputpath')

json_format = get_format('JSON')
gmlxml_format = get_format('GML')


class PavicsUpdate(Process):
    def __init__(self):
        self.solr_server = os.environ.get('SOLR_HOST', None)
        # The combination of the 'source' and 'url' fields provide the 'id'
        # in the Solr database, they both must be provided.
        inputs = [LiteralInput('id',
                               'id field of the dataset or file',
                               abstract='id field of the dataset or file.',
                               data_type='string'),
                  LiteralInput('type',
                               'Dataset or File',
                               abstract=('The File type will update a single '
                                         'file, the Dataset type will update '
                                         'all documents sharing its '
                                         'dataset_id'),
                               data_type='string',
                               default='File',
                               min_occurs=0,
                               mode=None),
                  LiteralInput('updates',
                               'Fields to update with their new values',
                               abstract=('Format is '
                                         'key1:value1,key2:value2,...'),
                               data_type='string')]
        outputs = [ComplexOutput('update_result',
                                 'PAVICS Catalogue Update Result',
                                 abstract='Update result as a json.',
                                 supported_formats=[json_format])]
        outputs[0].as_reference = True

        super(PavicsUpdate, self).__init__(
            self._handler,
            identifier='pavicsupdate',
            title='PAVICS Catalogue Update',
            abstract=('Update database entries using key:value pairs and '
                      'identified by their ids.'),
            version='0.1',
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True)

    def _handler(self, request, response):
        # Get the source and url to setup the update dictionary.
        update_id = request.inputs['id'][0].data
        if 'type' in request.inputs:
            update_type = request.inputs['type'][0].data
        else:
            update_type = 'File'
        if update_type == 'File':
            update_dict = {'id': update_id}
        elif update_type == 'Dataset':
            update_dict = {'dataset_id': update_id}
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
            update_dict.update({kv[0]: kv[1]})

        try:
            update_result = catalog.pavicsupdate(self.solr_server, update_dict)
        except:
            raise Exception(traceback.format_exc())

        # Here we construct a unique filename
        time_str = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        output_file_name = "solr_result_{0}_.json".format(time_str)
        output_file = os.path.join(json_output_path, output_file_name)
        f1 = open(output_file, 'w')
        f1.write(json.dumps(update_result))
        f1.close()
        response.outputs['update_result'].file = output_file
        response.outputs['update_result'].output_format = json_format
        return response
