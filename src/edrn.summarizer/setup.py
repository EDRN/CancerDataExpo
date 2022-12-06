# encoding: utf-8
# Copyright 2008-2011 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from setuptools import setup, find_packages
import os.path

# Package data
# ------------

_name            = 'edrn.summarizer'
_version         = '0.0.8'
_description     = 'EDRN Summarizer Server'
_author          = 'David Liu'
_authorEmail     = 'david.liu@jpl.nasa.gov'
_maintainer      = 'David Liu'
_maintainerEmail = 'david.liu@jpl.nasa.gov'
_license         = 'ALv2'
_namespaces      = ['edrn']
_zipSafe         = False
_keywords        = 'summary summarizer web zope plone cancer bioinformatics detection informatics edrn'
_testSuite       = 'edrn.summarizer.tests.test_suite'
_entryPoints     = {
    'z3c.autoinclude.plugin': ['target=plone'],
}
_requirements = [
    'collective.autopermission',
    'Pillow',
    'plone.app.dexterity [relations]',
    'z3c.relationfield',
    'plone.app.relationfield',
    'plone.rest',
    'plone.behavior',
    'Products.CMFPlone',
    'rdflib==6.2.0',
    'mygene',
    'requests',
    'biopython',
    'setuptools',
    'suds2',
]
_extras = {
    'test': ['plone.app.testing', 'rdfextras'],
}
_classifiers = [
    'Development Status :: 4 - Beta',
    'Environment :: Web Environment',
    'Framework :: Plone',
    'Intended Audience :: Healthcare Industry',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: Apache Software License',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Topic :: Internet :: WWW/HTTP',
    'Topic :: Scientific/Engineering :: Bio-Informatics',
    'Topic :: Software Development :: Libraries :: Python Modules',
]

# Setup Metadata
# --------------

def _read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

_header = '*' * len(_name) + '\n' + _name + '\n' + '*' * len(_name)
_longDescription = _header + '\n\n' + _read('README.rst') + '\n\n' + _read('docs', 'INSTALL.txt') + '\n\n' \
    + _read('docs', 'HISTORY.txt') + '\n'
open('doc.txt', 'w').write(_longDescription)

setup(
    author=_author,
    author_email=_authorEmail,
    classifiers=_classifiers,
    description=_description,
    entry_points=_entryPoints,
    extras_require=_extras,
    include_package_data=True,
    install_requires=_requirements,
    keywords=_keywords,
    license=_license,
    long_description=_longDescription,
    maintainer=_maintainer,
    maintainer_email=_maintainerEmail,
    name=_name,
    namespace_packages=_namespaces,
    packages=find_packages(exclude=['ez_setup', 'distribute_setup', 'bootstrap']),
    url='https://github.com/EDRN/' + _name,
    version=_version,
    zip_safe=_zipSafe,
)
