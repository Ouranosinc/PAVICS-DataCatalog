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
            self.config_dict = dict(self.config.items('pavicrawler'))
        except ConfigParser.NoSectionError:
            self.config_dict = {'wps_host': ''}
        self.wps_host = self.config_dict['wps_host']
        self.solr_host = self.config_dict.get('solr_host', None)
        self.thredds_host = self.config_dict.get('thredds_host', None)
        self.wms_alternate_server = self.config_dict.get(
            'wms_alternate_server', None)
        if not self.wps_host:
            if self.solr_host:
                os.environ['SOLR_HOST'] = self.solr_host
            if self.thredds_host:
                os.environ['THREDDS_HOST'] = self.thredds_host
            if self.wms_alternate_server:
                os.environ['WMS_ALTERNATE_SERVER'] = self.wms_alternate_server
            try:
                from pavics_datacatalog.wps_processes import \
                    PavicsCrawler, PavicsSearch
            except ImportError:
                sys.path.append(os.path.join(
                    '/'.join(os.getcwd().split('/')[:-1]), 'wps_processes'))
                from wps_pavicrawler import PavicsCrawler
                from wps_pavicsearch import PavicsSearch
            self.client = WpsClient(
                Service(processes=[PavicsCrawler(), PavicsSearch()]),
                WpsTestResponse)
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

    def test_process_exists_pavicrawler(self):
        html_response = wpsxml.wps_response(
            self.wps_host,
            '?service=WPS&request=GetCapabilities&version=1.0.0',
            self.client)
        processes = wpsxml.parse_getcapabilities(html_response)
        self.assertTrue('pavicrawler' in processes)

    def test_describeprocess_pavicrawler(self):
        html_response = wpsxml.wps_response(
            self.wps_host,
            ('?service=WPS&request=DescribeProcess&version=1.0.0&'
             'identifier=pavicrawler'),
            self.client)
        describe_process = wpsxml.parse_describeprocess(html_response)
        self.assertTrue('target_files' in describe_process['inputs'])
        self.assertTrue('crawler_result' in describe_process['outputs'])

    def test_pavicrawler_01(self):
        # Crawl, then search and WMS link validation
        if (not self.wps_host) and (not self.solr_host):
            raise unittest.SkipTest('Solr host not defined in config.')
        wpsxml.config_is_available(
            ['thredds_host', 'target_file', 'target_search', 'target_wms'],
            self.config_dict)
        html_response = wpsxml.wps_response(
            self.wps_host,
            ('?service=WPS&request=execute&version=1.0.0&'
             'identifier=pavicrawler&DataInputs='
             'target_files={0}').format(self.config_dict['target_file']),
            self.client)
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
