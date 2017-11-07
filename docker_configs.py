import os
import pwd
import ConfigParser


def make_dirs(name, user):
    mode = 0o755
    uid, gid = pwd.getpwnam(user)[2:4]
    if not os.path.isdir(name):
        os.makedirs(name, mode)
    else:
        os.chmod(name, mode)
    os.chown(name, uid, gid)


config = ConfigParser.RawConfigParser()
config.read('/home/catalog.cfg')
catalog_configs = ['SOLR_HOST', 'THREDDS_HOST', 'MAGPIE_HOST',
                   'WMS_ALTERNATE_SERVER', 'WPS_RESULTS',
                   'THREDDS_HOST_MAGPIE_SVC_NAME']
config_values = {}
for catalog_config in catalog_configs:
    try:
        config_values[catalog_config] = config.get('catalog', catalog_config)
    except ConfigParser.NoOptionError:
        config_values[catalog_config] = None

with open('/etc/apache2/envvars', 'a') as f:
    f.write('\n')
    for key, val in config_values.items():
        if (val is None) or (key == 'WPS_RESULTS'):
            continue
        f.write('export {0}="{1}"\n'.format(key, val))

with open('/etc/pywps.cfg', 'r') as f:
    pywps_config = f.read()

pywps_config = pywps_config.replace(
    'outputurl=placeholder_for_docker_run',
    'outputurl={0}'.format(config_values['WPS_RESULTS']))

with open('/etc/pywps.cfg', 'w') as f:
    f.write(pywps_config)

config = ConfigParser.RawConfigParser()
config.read('/etc/pywps.cfg')
outputpath = config.get('server', 'outputpath')
make_dirs(outputpath, 'apapywps')
