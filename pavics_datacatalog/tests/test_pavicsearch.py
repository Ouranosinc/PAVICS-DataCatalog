import os
import sys
import unittest
import ConfigParser
import json

from pywps import Service
from pywps.tests import WpsClient, WpsTestResponse

try:
    from pavics_datacatalog.tests import wpsxml
except ImportError:
    import wpsxml


class TestPavicsearch(unittest.TestCase):

    def setUp(self):
        self.config = ConfigParser.RawConfigParser()
        if os.path.isfile('configtests.cfg'):
            self.config.read('configtests.cfg')
        else:
            self.config.read('pavics_datacatalog/tests/configtests.cfg')
        try:
            self.config_dict = dict(self.config.items('pavicsearch'))
        except ConfigParser.NoSectionError:
            raise unittest.SkipTest('No pavicsearch section in config.')
        self.wps_host = self.config_dict['wps_host']
        self.solr_host = self.config_dict.get('solr_host', None)
        if not self.wps_host:
            if self.solr_host:
                os.environ['SOLR_HOST'] = self.solr_host
            try:
                from pavics_datacatalog.wps_processes import \
                    PavicsSearch
            except ImportError:
                sys.path.append(os.path.join(
                    '/'.join(os.getcwd().split('/')[:-1]), 'wps_processes'))
                from wps_pavicsearch import PavicsSearch
            self.client = WpsClient(
                Service(processes=[PavicsSearch()]), WpsTestResponse)
        else:
            self.client = None

    def test_getcapabilities(self):
        html_response = wpsxml.wps_response(
            self.wps_host,
            '?service=WPS&request=GetCapabilities&version=1.0.0',
            self.client)
        self.assertTrue(html_response)

    def test_getcapabilities_repeat(self):
        for i in range(10):
            html_response = wpsxml.wps_response(
                self.wps_host,
                '?service=WPS&request=GetCapabilities&version=1.0.0',
                self.client)
            self.assertTrue(html_response)

    def test_process_exists_pavicsearch(self):
        html_response = wpsxml.wps_response(
            self.wps_host,
            '?service=WPS&request=GetCapabilities&version=1.0.0',
            self.client)
        processes = wpsxml.parse_getcapabilities(html_response)
        self.assertTrue('pavicsearch' in processes)

    def test_describeprocess_pavicsearch(self):
        html_response = wpsxml.wps_response(
            self.wps_host,
            ('?service=WPS&request=DescribeProcess&version=1.0.0&'
             'identifier=pavicsearch'),
            self.client)
        describe_process = wpsxml.parse_describeprocess(html_response)
        self.assertTrue('facets' in describe_process['inputs'])
        self.assertTrue('search_result' in describe_process['outputs'])

    def test_pavicsearch_01(self):
        if (not self.wps_host) and (not self.solr_host):
            raise unittest.SkipTest('Solr host not defined in config.')
        html_response = wpsxml.wps_response(
            self.wps_host,
            ('?service=WPS&request=execute&version=1.0.0&'
             'identifier=pavicsearch&DataInputs='),
            self.client)
        outputs = wpsxml.parse_execute_response(html_response)
        self.assertTrue('search_result' in outputs['outputs'])

    def test_pavicsearch_02(self):
        # Search and WMS link validation
        if (not self.wps_host) and (not self.solr_host):
            raise unittest.SkipTest('Solr host not defined in config.')
        wpsxml.config_is_available(
            ['target_search', 'target_wms'], self.config_dict)
        html_response = wpsxml.wps_response(
            self.wps_host,
            ('?service=WPS&request=execute&version=1.0.0&'
             'identifier=pavicsearch&DataInputs='
             'type=File;query={0}').format(self.config_dict['target_search']),
            self.client)
        outputs = wpsxml.parse_execute_response(html_response)
        search_json = wpsxml.get_wps_xlink(outputs['outputs']['search_result'])
        search_json = json.loads(search_json)
        self.assertEqual(search_json['response']['docs'][0]['wms_url'],
                         self.config_dict['target_wms'])

suite = unittest.TestLoader().loadTestsFromTestCase(TestPavicsearch)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
