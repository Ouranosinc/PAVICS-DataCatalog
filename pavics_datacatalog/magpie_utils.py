import os
import requests
import json


class MagpieService:
    def __init__(self, magpie_url, magpie_thredds_services, token):
        permission = 'read'
        magpie_url = magpie_url.strip('/')
        session = requests.Session()
        if token:
            session.cookies.set('auth_tkt', token)
        response = session.get(magpie_url + '/users/current/services')
        if response.status_code != 200:
            raise response.raise_for_status()

        services = json.loads(response.text)
        self.allowed_urls = []
        for key, service in services['services']['thredds'].items():
            thredds_svc = service['service_name']
            if thredds_svc not in magpie_thredds_services:
                continue

            magpie_path = 'users/current/services/{svc}/resources'.format(
                token=token, svc=thredds_svc)
            response = session.get(os.path.join(magpie_url, magpie_path))
            if response.status_code != 200:
                raise response.raise_for_status()

            response_data = json.loads(response.text)
            service = response_data['service']

            thredds_host = magpie_thredds_services[thredds_svc].strip('/')
            if permission in service['permission_names']:
                self.allowed_urls.append(thredds_host)
            else:
                for c_id, resource_tree in service['resources'].items():
                    for resource_path in self.tree_parser(
                            resource_tree, permission,
                            '/'.join([thredds_host, 'fileServer'])):
                        self.allowed_urls.append(resource_path.strip('/'))

    def tree_parser(self, resources_tree, permission, url):
        url = '/'.join([url, resources_tree['resource_name']])
        if permission in resources_tree['permission_names']:
            yield url

        for r_id, resource in resources_tree['children'].items():
            for resource_path in self.tree_parser(resource, permission, url):
                yield resource_path

    def has_view_perm(self, thredds_url):
        for url in self.allowed_urls:
            if url in thredds_url:
                return True
        return False
