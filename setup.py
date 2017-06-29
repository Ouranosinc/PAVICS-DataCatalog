import os, glob

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.md')).read()

reqs = ['pywps', 'pavics']

classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Science/Research',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Atmospheric Science',
        ]

setup(name='pavics_datacatalog',
      version='0.2',
      description='Processes for data catalog interactions',
      long_description=README + '\n\n' + CHANGES,
      classifiers=classifiers,
      author='Blaise Gauvin St-Denis',
      author_email='gauvin-stdenis.blaise@ouranos.ca',
      url='https://github.com/Ouranosinc/PAVICS-DataCatalog',
      license = "http://www.apache.org/licenses/LICENSE-2.0",
      keywords='wps  pywps pavics conda climate data catalog solr',
      packages=find_packages(),
      #py_modules = [os.path.splitext(f)[0] for f in glob.glob('wps_processes/wps_*.py')], 
      include_package_data=True,
      zip_safe=False,
      test_suite='',
      install_requires=reqs,
      entry_points = {
          'console_scripts': [
              ]}     
      ,
      )