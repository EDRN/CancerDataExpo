# encoding: utf-8
# Copyright 2012–2020 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from plone.app.dexterity.behaviors.exclfromnav import IExcludeFromNavigation
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.file import NamedBlobImage
from plone.registry.interfaces import IRegistry
from Products.CMFCore.interfaces import IFolderish
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.WorkflowCore import WorkflowException
from zope.component import getUtility
import pkg_resources, plone.api


_homePage = '''
<p>The Cancer Data Expo is a marketplace, exchange, and bazaar for cancer data for
the <a href='https://edrn.nci.nih.gov/'>Early Detection Research Network</a> 
in the form of ReST-based web APIs. It provides data, information, and knowledge
using <a href='https://www.w3.org/RDF/'>RDF</a> and
<a href='https://www.json.org/json-en.html'>JSON</a>.
</p>
<h2>📀 Data Sources</h2>
<ul>
<li><a href='rdf-data'>RDF</a> from the DMCC's incredibly brave SOAP API</li>
<li><a href='summarizer-data'>JSON</a> summaries of that same information</li>
</ul>
<h3>🔧 Configuration</h3>
<ul>
<li><a href='rdf-generators'>RDF Generators</a></li>
<li><a href='summarizer-generators'>Summarizer Generators</a></li>
</ul>
'''

_photosDescription = '''The RDF for people refers to photographs of some of them and there's no better place than here to host these photos.'''


def publish(item, wfTool=None):
    if wfTool is None:
        wfTool = getToolByName(item, 'portal_workflow')
    try:
        wfTool.doActionFor(item, action='publish')
        item.reindexObject()
    except WorkflowException:
        pass
    if IFolderish.providedBy(item):
        for itemID, subItem in item.contentItems():
            publish(subItem, wfTool)


def setUpHomePage(portal):
    frontPage = plone.api.content.get('/front-page')
    if frontPage is None:
        frontPage = createContentInContainer(portal, 'Document', id='front-page')
    frontPage.title = 'Welcome to the Cancer Data Expo'
    frontPage.description = 'A web-based API gateway to cancer data, information, and knowledge.'
    frontPage.text = RichTextValue(_homePage, 'text/html', 'text/x-html-safe')
    adapter = IExcludeFromNavigation(frontPage, None)
    if adapter is not None:
        adapter.exclude_from_nav = True
    portal.setDefaultPage('front-page')
    publish(portal['front-page'])
    frontPage.reindexObject()


def loadPhotographs(portal):
    if 'staff-photographs' in list(portal.keys()): return
    folder = createContentInContainer(
        portal,
        'Folder',
        id='staff-photographs',
        title='Staff Photographs',
        description=_photosDescription
    )
    photos = (
        ('piPhoto5.gif', 'Ziding, Feng', 'EDRN Principal Investigator, Statistical Methods In Cancer.'),
        ('piPhoto67.gif', 'Brenner, Dean', 'EDRN Principal Investigator.'),
        ('piPhoto68.gif', 'Chia, David', 'EDRN Principal Investigator.'),
        ('piPhoto81.gif', 'Marks, Jeffrey', 'EDRN Principal Investigator, Molecular Biology.'),
        ('piPhoto82.gif', 'Meltzer, Stephen', 'EDRN Principal Investigator, GI/Oncology/Gastroenterology.'),
        ('piPhoto84.gif', 'Rom, William', 'EDRN Principal Investigator, Pulmonary Medicine.'),
        ('piPhoto87.gif', 'Srivastava, Sudhir', 'EDRN Principal Investigator, Molecular Screening and Detection.'),
        ('piPhoto92.gif', 'Semmes, John', 'EDRN Principal Investigator, Microbiology and Molecular.'),
        ('piPhoto150.gif', 'Fishman, David', 'Associate Member, Gynecologic Oncology.'),
        ('piPhoto151.gif', 'Hanash, Samir', 'EDRN Principal Investigator.'),
        ('piPhoto167.gif', 'Loshkin, Anna', 'EDRN Principal Investigator.'),
        ('piPhoto188.gif', 'Chinnaiyan, Arul', 'EDRN Principal Investigator.'),
        ('piPhoto192.gif', 'Liu, Alvin', 'EDRN Principal Investigator.'),
        ('piPhoto201.gif', 'Stass, Sanford', 'EDRN Principal Investigator.'),
        ('piPhoto202.gif', 'Engstrom, Paul', 'EDRN Principal Investigator.'),
        ('piPhoto203.gif', 'Sanda, Martin', 'EDRN Principal Investigator.'),
        ('piPhoto232.gif', 'Tainsky, Michael', 'EDRN Principal Investigator.'),
    )
    for fn, name, desc in photos:
        with pkg_resources.resource_stream(__name__, 'photos/' + fn) as f:
            createContentInContainer(
                folder,
                'Image',
                id=fn,
                title=name,
                description=desc,
                image=NamedBlobImage(data=f.read(), contentType='image/gif', filename=fn)
            )
    folder.setLayout('album_view')
    publish(portal['staff-photographs'])


def hideFolders(portal):
    for i in ('news', 'events', 'Members'):
        folder = plone.api.content.get('/' + i)
        if folder is None: continue
        plone.api.content.delete(obj=folder)
    for i in ('rdf-generators', 'summarizer-generators'):
        folder = plone.api.content.get('/' + i)
        if folder is None: continue
        adapter = IExcludeFromNavigation(folder, None)
        if adapter is None: continue
        adapter.exclude_from_nav = True


def setupVarious(context):
    if context.readDataFile('edrndmcc.appserver.marker.txt') is None: return
    portal = context.getSite()
    setUpHomePage(portal)
    loadPhotographs(portal)
    hideFolders(portal)
    # I've tried setting this in ``registry.xml`` but it doesn't "take". Trying here:
    registry = getUtility(IRegistry)
    registry['plone.filter_on_workflow'] = True
    plone.api.portal.get_tool('portal_catalog').clearFindAndRebuild()
