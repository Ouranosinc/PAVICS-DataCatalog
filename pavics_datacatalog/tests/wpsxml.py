import unittest
from lxml import etree
try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request


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


def parse_execute_response(html_response):
    d = {}
    d['outputs'] = {}
    root = etree.fromstring(html_response)
    lvl1 = children_as_dict(root.getchildren())
    lvl2 = children_as_dict(lvl1['wps:Status'][0].getchildren())
    if 'wps:ProcessSucceeded' in lvl2:
        d['status'] = 'ProcessSucceeded'
    elif 'wps:ProcessFailed' in lvl2:
        d['status'] = 'ProcessFailed'
        return d
    lvl2 = children_as_dict(lvl1['wps:ProcessOutputs'][0].getchildren())
    for element in lvl2['wps:Output']:
        lvl3 = children_as_dict(element.getchildren())
        key = lvl3['ows:Identifier'][0].text
        if 'wps:Data' in lvl3:
            d['outputs'][key] = lvl3['wps:Data'][0].getchildren()[0].text
        elif 'wps:Reference' in lvl3:
            d['outputs'][key] = lvl3['wps:Reference'][0].values()[0]
    return d


def wps_response(wps_host, pywps_request, wps_client=None):
    if wps_host:
        url_request = Request(
            url='http://{0}/pywps{1}'.format(wps_host, pywps_request))
        url_response = urlopen(url_request)
        return url_response.read()
    else:
        resp = wps_client.get(pywps_request)
        return resp.get_data()


def get_wps_xlink(xlink):
    url_request = Request(url=xlink)
    url_response = urlopen(url_request)
    return url_response.read()


def config_is_available(config_names, config_dict):
    if not hasattr(config_names, '__iter__'):
        config_names = [config_names]
    for config_name in config_names:
        if (config_name not in config_dict) or (not config_dict[config_name]):
            raise unittest.SkipTest(
                "{0} not defined in config.".format(config_name))
