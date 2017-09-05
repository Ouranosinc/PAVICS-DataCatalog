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


class TestGetPoint(unittest.TestCase):

    def setUp(self):
        self.config = ConfigParser.RawConfigParser()
        if os.path.isfile('configtests.cfg'):
            self.config.read('configtests.cfg')
        else:
            self.config.read('pavics_datacatalog/tests/configtests.cfg')
        try:
            self.config_dict = dict(self.config.items('getpoint'))
        except ConfigParser.NoSectionError:
            self.config_dict = {'wps_host': ''}
        self.wps_host = self.config_dict['wps_host']
        if not self.wps_host:
            try:
                from pavics_datacatalog.wps_processes import GetPoint
            except ImportError:
                sys.path.append(os.path.join(
                    '/'.join(os.getcwd().split('/')[:-1]), 'wps_processes'))
                from wps_getpoint import GetPoint
            self.client = WpsClient(
                Service(processes=[GetPoint()]), WpsTestResponse)
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

    def test_process_exists_getpoint(self):
        html_response = wpsxml.wps_response(
            self.wps_host,
            '?service=WPS&request=GetCapabilities&version=1.0.0',
            self.client)
        processes = wpsxml.parse_getcapabilities(html_response)
        self.assertTrue('getpoint' in processes)

    def test_describeprocess_getpoint(self):
        html_response = wpsxml.wps_response(
            self.wps_host,
            ('?service=WPS&request=DescribeProcess&version=1.0.0&'
             'identifier=getpoint'),
            self.client)
        describe_process = wpsxml.parse_describeprocess(html_response)
        self.assertTrue('opendap_url' in describe_process['inputs'])
        self.assertTrue('point_result' in describe_process['outputs'])

    def test_getpoint_01(self):
        wpsxml.config_is_available(
            ['netcdf_file', 'var_name', 'nearest_lon', 'nearest_lat',
             'nearest_time', 'point_value', 'precision'], self.config_dict)
        format_inputs = [self.config_dict['netcdf_file'],
                         self.config_dict['var_name'],
                         self.config_dict['nearest_lon'],
                         self.config_dict['nearest_lat'],
                         self.config_dict['nearest_time']]
        html_response = wpsxml.wps_response(
            self.wps_host,
            ('?service=WPS&request=execute&version=1.0.0&'
             'identifier=getpoint&DataInputs='
             'opendap_url={0};variable={1};nearest_to=lon:{2};'
             'nearest_to=lat:{3};nearest_to=time:{4}').format(*format_inputs),
            self.client)
        outputs = wpsxml.parse_execute_response(html_response)
        search_json = wpsxml.get_wps_xlink(outputs['outputs']['point_result'])
        search_json = json.loads(search_json)
        self.assertAlmostEqual(
            float(search_json[self.config_dict['var_name']]['value']),
            float(self.config_dict['point_value']),
            places=int(self.config_dict['precision']))

suite = unittest.TestLoader().loadTestsFromTestCase(TestGetPoint)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
