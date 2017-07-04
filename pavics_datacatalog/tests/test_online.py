import unittest
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request
from lxml import etree


def children_as_dict(list_of_element):
    d = {}
    for i, element in enumerate(list_of_element):
        element_tag = element.tag
        for key, nsvalue in element.nsmap.items():
            element_tag = element_tag.replace('{' + nsvalue + '}', key + ':')
        if element_tag in d:
            d[element_tag].append(element)
        else:
            d[element_tag] = [element]
    return d


def parse_getcapabilities(html_response):
    processes = []
    root = etree.fromstring(html_response)
    lvl1 = children_as_dict(root.getchildren())
    lvl2 = children_as_dict(lvl1['wps:ProcessOfferings'][0].getchildren())
    for element in lvl2['wps:Process']:
        lvl3 = children_as_dict(element.getchildren())
        processes.append(lvl3['ows:Identifier'][0].text)
    return sorted(processes)


def parse_describeprocess(html_response):
    d = {}
    root = etree.fromstring(html_response)
    lvl1 = children_as_dict(root.getchildren())
    lvl2 = children_as_dict(lvl1['ProcessDescription'][0])
    inputs = []
    for element in lvl2['DataInputs']:
        lvl3 = children_as_dict(element.getchildren())
        lvl4 = children_as_dict(lvl3['Input'][0].getchildren())
        inputs.append(lvl4['ows:Identifier'][0].text)
    outputs = []
    for element in lvl2['ProcessOutputs']:
        lvl3 = children_as_dict(element.getchildren())
        lvl4 = children_as_dict(lvl3['Output'][0].getchildren())
        outputs.append(lvl4['ows:Identifier'][0].text)
    d['inputs'] = inputs
    d['outputs'] = outputs
    return d


class TestOnline(unittest.TestCase):

    def test_getcapabilities(self):
        url_request = Request(
            url=('http://localhost:8009/pywps?service=WPS&request='
                 'GetCapabilities&version=1.0.0'))
        try:
            url_response = urlopen(url_request)
        except Exception as e:
            self.fail(e.reason)
        html_response = url_response.read()
        self.assertTrue(html_response)

    def test_getcapabilities_10_times(self):
        for i in range(10):
            url_request = Request(
                url=('http://localhost:8009/pywps?service=WPS&request='
                     'GetCapabilities&version=1.0.0'))
            try:
                url_response = urlopen(url_request)
            except Exception as e:
                self.fail(e.reason)
            html_response = url_response.read()
            self.assertTrue(html_response)

    def test_process_exists_pavicrawler(self):
        url_request = Request(
            url=('http://localhost:8009/pywps?service=WPS&request='
                 'GetCapabilities&version=1.0.0'))
        try:
            url_response = urlopen(url_request)
        except Exception as e:
            self.fail(e.reason)
        html_response = url_response.read()
        processes = parse_getcapabilities(html_response)
        self.assertTrue('pavicrawler' in processes)

    def test_describeprocess_pavicrawler(self):
        url_request = Request(
            url=('http://localhost:8009/pywps?service=WPS&request='
                 'DescribeProcess&version=1.0.0&identifier=pavicrawler'))
        try:
            url_response = urlopen(url_request)
        except Exception as e:
            self.fail(e.reason)
        html_response = url_response.read()
        describe_process = parse_describeprocess(html_response)
        self.assertTrue('target_files' in describe_process['inputs'])
        self.assertTrue('crawler_result' in describe_process['outputs'])

suite = unittest.TestLoader().loadTestsFromTestCase(TestOnline)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite)
