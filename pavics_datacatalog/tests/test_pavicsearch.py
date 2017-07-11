import os
import sys
import unittest
import ConfigParser

from pywps import Service
from pywps.tests import WpsClient, WpsTestResponse

try:
    from pavics_datacatalog.tests.wpsxml import parse_getcapabilities,\
        parse_describeprocess, parse_execute_response, wps_response
except ImportError:
    from wpsxml import parse_getcapabilities,\
        parse_describeprocess, parse_execute_response, wps_response


class TestPavicsearch(unittest.TestCase):

    def setUp(self):
        self.config = ConfigParser.RawConfigParser()
        self.config.read('configtests.cfg')
        self.wps_host = dict(self.config.items('pavicsearch'))['wps_host']
        self.solr_host = dict(self.config.items('pavicsearch'))['solr_host']
        if not self.wps_host:
            os.environ['SOLR_HOST'] = self.solr_host
            try:
                from pavics_datacatalog.tests.wps_pavicsearch import \
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
        html_response = wps_response(
            self.wps_host,
            '?service=WPS&request=GetCapabilities&version=1.0.0',
            self.client)
        self.assertTrue(html_response)

    def test_getcapabilities_repeat(self):
        for i in range(10):
            html_response = wps_response(
                self.wps_host,
                '?service=WPS&request=GetCapabilities&version=1.0.0',
                self.client)
            self.assertTrue(html_response)

    def test_process_exists_pavicsearch(self):
        html_response = wps_response(
            self.wps_host,
            '?service=WPS&request=GetCapabilities&version=1.0.0',
            self.client)
        processes = parse_getcapabilities(html_response)
        self.assertTrue('pavicsearch' in processes)

    def test_describeprocess_pavicsearch(self):
        html_response = wps_response(
            self.wps_host,
            ('?service=WPS&request=DescribeProcess&version=1.0.0&'
             'identifier=pavicsearch'),
            self.client)
        describe_process = parse_describeprocess(html_response)
        self.assertTrue('facets' in describe_process['inputs'])
        self.assertTrue('search_result' in describe_process['outputs'])

    def test_pavicsearch_01(self):
        solr_host = dict(self.config.items('pavicsearch'))['solr_host']
        if not solr_host:
            raise unittest.SkipTest('Solr host not defined in config.')
        html_response = wps_response(
            self.wps_host,
            ('?service=WPS&request=execute&version=1.0.0&'
             'identifier=pavicsearch&DataInputs='),
            self.client)
        outputs = parse_execute_response(html_response)
        self.assertTrue('search_result' in outputs['outputs'])

suite = unittest.TestLoader().loadTestsFromTestCase(TestPavicsearch)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
