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


catalog_config_fn = '/home/catalog.cfg'
pywps_config_fn = '/etc/pywps.cfg'
apache_envvars_fn = '/etc/apache2/envvars'


# Export apache environment variables from the catalog config
config = ConfigParser.RawConfigParser()
config.read(catalog_config_fn)
with open(apache_envvars_fn, 'a') as f:
    f.write('\n')
    for cfg, val in config.items('catalog'):
        f.write('export {0}="{1}"\n'.format(cfg.upper(), val))

# Update pywps config using the catalog pywps section
pywps_config = ConfigParser.RawConfigParser()
pywps_config.read(pywps_config_fn)
for cfg, val in config.items('pywps'):
    try:
        pywps_config.set('server', cfg, val)
    except ConfigParser.NoSectionError:
        pass
for cfg, val in config.items('logging'):
    try:
        pywps_config.set('logging', cfg, val)
    except ConfigParser.NoSectionError:
        pass
with open(pywps_config_fn, 'w') as f:
    pywps_config.write(f)

# Make sure the output path exists
outputpath = pywps_config.get('server', 'outputpath')
make_dirs(outputpath, 'apapywps')
