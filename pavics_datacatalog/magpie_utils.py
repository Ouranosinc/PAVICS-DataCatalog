import os
import requests
import json


class MagpieService:
    def __init__(self, magpie_url, magpie_thredds_services, token, verify=True):
        permission = 'read'
        magpie_url = magpie_url.rstrip('/')
        session = requests.Session()
        if token:
            session.cookies.set('auth_tkt', token)
        response = session.get(
            magpie_url + '/users/current/services', 
            params={'inherit': True, 'cascade': True},
            verify=verify,
        )
        response.raise_for_status()

        services = response.json()
        self.allowed_urls = []
        if 'thredds' not in services['services']:
            return
        for service in services['services']['thredds'].values():
            thredds_service_name = service['service_name']
            if thredds_service_name not in magpie_thredds_services:
                continue

            resources_url = '{url}/users/current/services/{svc}/resources'.format(
                url=magpie_url, 
                svc=thredds_service_name
            )
            response = session.get(resources_url, params={'inherit': True}, verify=verify)
            response.raise_for_status()

            service_resources = response.json()['service']

            thredds_host = magpie_thredds_services[thredds_service_name].strip('/')
            if permission in service['permission_names']:
                self.allowed_urls.append(thredds_host)
            else:
                for c_id, resource_tree in service_resources['resources'].items():
                    for resource_path in self.tree_parser(
                        resource_tree, 
                        permission,
                        '/'.join([thredds_host, 'fileServer'])
                    ):
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
