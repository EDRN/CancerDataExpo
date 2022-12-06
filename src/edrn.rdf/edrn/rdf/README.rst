This package provides an RDF-based web service that describes the knowledge
assets of the Early Detection Research Network (EDRN).


Functional Tests
================

To demonstrate the code, we'll classes in a series of functional tests.  And
to do so, we'll need a test browser::

    >>> app = layer['app']
    >>> from plone.testing.z2 import Browser
    >>> from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD
    >>> browser = Browser(app)
    >>> browser.handleErrors = False
    >>> browser.addHeader('Authorization', 'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD))
    >>> portal = layer['portal']    
    >>> portalURL = portal.absolute_url()

Here we go.


RDF Source
==========

An RDF Source is a source of RDF data.  They can be added anywhere in the
portal::


    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='edrn-rdf-rdfsource')
    >>> l.url.endswith('++add++edrn.rdf.rdfsource')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = 'A Simple Source'
    >>> browser.getControl(name='form.widgets.description').value = "It's just for functional tests."
    >>> browser.getControl(name='form.widgets.active:list').value = False
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'a-simple-source' in portal.keys()
    True
    >>> source = portal['a-simple-source']
    >>> source.title
    'A Simple Source'
    >>> source.description
    "It's just for functional tests."
    >>> source.active
    False

Now, these things are supposed to produce RDF when called with the appropriate
view.  Does it?

    >>> browser.open(portalURL + '/a-simple-source/@@rdf')
    Traceback (most recent call last):
    ...
    ValueError: The RDF Source at /plone/a-simple-source does not have an active RDF file to send

It doesn't because it hasn't yet made any RDF files to send, and it can't do
that without an RDF generator.  RDF Sources get their data from RDF
Generators.


RDF Generators
==============

RDF Generators have the responsibility of accessing various sources of data
(notably the DMCC's web service) and yielding an RDF graph, suitable for
serializing into XML or some other format.  There are several kinds available.


Null RDF Generator
------------------

One such generator does absolutely nothing: it's the Null RDF Generator, and
all it ever does it make zero statements about anything.  It's not very
useful, but it's nice to have for testing.  Check it out::

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='edrn-rdf-nullrdfgenerator')
    >>> l.url.endswith('++add++edrn.rdf.nullrdfgenerator')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = 'Silence'
    >>> browser.getControl(name='form.widgets.description').value = 'Just for testing.'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'silence' in portal.keys()
    True
    >>> generator = portal['silence']
    >>> generator.title
    'Silence'
    >>> generator.description
    'Just for testing.'

We'll set up our RDF source with this generator; we'd do this "though the web"
but by Plone 5.1 there's so much "magic" and "protection" around form
submission that we can't anymore:

    >>> from z3c.relationfield import RelationValue
    >>> from zope.app.intid.interfaces import IIntIds
    >>> from zope.component import getUtility
    >>> intIDs = getUtility(IIntIds)
    >>> source.generator = RelationValue(intIDs.getId(generator))
    >>> import transaction
    >>> transaction.commit()
    >>> source.generator.to_object.title
    'Silence'

The RDF source still doesn't produce any RDF, though::

    >>> browser.open(portalURL + '/a-simple-source/@@rdf')
    Traceback (most recent call last):
    ...
    ValueError: The RDF Source at /plone/a-simple-source does not have an active RDF file to send

That's because having the generator isn't enough.  Someone has to actually
*run* the generator.


Running the Generators
----------------------

Tickled by either a cron job or a Zope clock event, a special URL finds every
RDF source and asks it to run its generator to produce a fresh update.  Each
RDF source may (in the future) run its validators against the generated graph
to ensure it has the expected information.  Assuming it passes muster, the
source then saves that output as the latest and greatest RDF to deliver when
demanded.

Tickling::

    >>> browser.open(portalURL + '/@@updateRDF')  # 1

And is there any RDF?  Let's check::

    >>> browser.open(portalURL + '/a-simple-source/@@rdf')
    Traceback (most recent call last):
    ...
    ValueError: The RDF Source at /plone/a-simple-source does not have an active RDF file to send

Still no RDF?!  Right, because RDF Sources can be active or not.  If they're
active, then when it's time to generate RDF their generator will actually get
run.  But the source "A Simple Source" is *not* active.  We didn't check the
active box when we made it.  So, let's fix that and re-tickle::

    >>> browser.open(portalURL + '/a-simple-source/edit')
    >>> browser.getControl(name='form.widgets.active:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> source.generator.to_object.title
    'Silence'
    >>> source.active
    True
    >>> browser.open(portalURL + '/@@updateRDF')  # 2
    >>> browser.contents
    '...Sources updated:...<span id="numberSuccesses">1</span>...'

That looks promising: one source got updated.  I hope it was our simple source::

    >>> browser.open(portalURL + '/a-simple-source/@@rdf')
    >>> browser.isHtml
    False
    >>> browser.headers['content-type']
    'application/rdf+xml'
    >>> browser.contents
    b'<?xml version="1.0" encoding="utf-8"?>\n<rdf:RDF\n  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\n/>\n'

Finally, an RDF graph that makes absolutely no statements!

    The Simple Source now contains a single File object:
    >>> len(source.keys())
    1
    >>> generatedFileID = source.keys()[0]
    >>> source.approvedFile.to_object.id == generatedFileID
    True

If we re-generate all active RDF, the generator will detect that new file
matches the old and won't bother changing anything in the source::

    >>> browser.open(portalURL + '/@@updateRDF')  # 3
    >>> browser.contents
    '...Sources updated:...<span id="numberSuccesses">0</span>...'
    >>> source.approvedFile.to_object.id == generatedFileID
    True

By the way, that "updateRDF" is a Zope view that's available at the site root
only::

    >>> browser.open(portalURL + '/a-simple-source/@@updateRDF')
    Traceback (most recent call last):
    ...
    zExceptions.NotFound: .../a-simple-source/@@updateRDF

Now, how about some RDF that *makes a statement*?


Simple DMCC RDF Generator
-------------------------

The Simple DMCC RDF Generator uses straightforward mappings of the DMCC's
terrible web service output and into RDF statements.  They can be created
anywhere:

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='edrn-rdf-simpledmccrdfgenerator')
    >>> l.url.endswith('++add++edrn.rdf.simpledmccrdfgenerator')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = 'Organs'
    >>> browser.getControl(name='form.widgets.description').value = 'Generates lists of organs.'
    >>> browser.getControl(name='form.widgets.webServiceURL').value = 'testscheme://localhost/ws_newcompass.asmx?WSDL'
    >>> browser.getControl(name='form.widgets.operationName').value = 'Body_System'
    >>> browser.getControl(name='form.widgets.verificationNum').value = '0'
    >>> browser.getControl(name='form.widgets.uriPrefix').value = 'urn:testing:data:organ:'
    >>> browser.getControl(name='form.widgets.identifyingKey').value = 'Identifier'
    >>> browser.getControl(name='form.widgets.typeURI').value = 'urn:testing:types:organ'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'organs' in portal.keys()
    True
    >>> generator = portal['organs']
    >>> generator.title
    'Organs'
    >>> generator.description
    'Generates lists of organs.'
    >>> generator.webServiceURL
    'testscheme://localhost/ws_newcompass.asmx?WSDL'
    >>> generator.operationName
    'Body_System'
    >>> generator.verificationNum
    '0'
    >>> generator.uriPrefix
    'urn:testing:data:organ:'
    >>> generator.identifyingKey
    'Identifier'
    >>> generator.typeURI
    'urn:testing:types:organ'

We've got the generator, but we need to tell it how to map from the DMCC's
awful quasi-XML tags and into RDF predicates.  To do so, we add Predicate
Handlers to the Simple DMCC RDF Generator.  There are a few kinds:

• Literal Predicate Handlers that map a clumsy DMCC key to a predicate whose
  object is a literal value.
• Reference Predicate Handlers that map an inept DMCC key to a predicate whose
  object is a reference to another object, identified by its subject URI.
• Multi Literal Predicate Handlers map an awkward DMCC key that contains
  values separated by commas to multiple statements, one object per
  comma-separated value.
• Various specialized handlers for DMCC's other cumbersome cases.

Note that predicate handlers must be added to Simple DMCC RDF Generators; they
can't be added elsewhere::

    >>> browser.open(portalURL)
    >>> browser.getLink(id='edrn-rdf-literalpredicatehandler')
    Traceback (most recent call last):
    ...
    zope.testbrowser.browser.LinkNotFoundError


Literal Predicate Handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~

For organs, we need only to use the Literal Predicate Handler::

    >>> browser.open(portalURL + '/organs')
    >>> l = browser.getLink(id='edrn-rdf-literalpredicatehandler')
    >>> l.url.endswith('++add++edrn.rdf.literalpredicatehandler')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = 'item_Title'
    >>> browser.getControl(name='form.widgets.description').value = 'Maps the <item_Title> key to the Dublin Core title predicate URI.'
    >>> browser.getControl(name='form.widgets.predicateURI').value = 'http://purl.org/dc/terms/title'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'item_title' in generator.keys()
    True
    >>> predicateHandler = generator['item_title']
    >>> predicateHandler.title
    'item_Title'
    >>> predicateHandler.description
    'Maps the <item_Title> key to the Dublin Core title predicate URI.'
    >>> predicateHandler.predicateURI
    'http://purl.org/dc/terms/title'

That takes care of mapping <Title> to http://purl.org/dc/terms/title.  Now for
the <Description> key in the blundering DMCC output::

    >>> browser.open(portalURL + '/organs')
    >>> browser.getLink(id='edrn-rdf-literalpredicatehandler').click()
    >>> browser.getControl(name='form.widgets.title').value = 'Description'
    >>> browser.getControl(name='form.widgets.description').value = 'Maps the <Description> key to the DC description term.'
    >>> browser.getControl(name='form.widgets.predicateURI').value = 'http://purl.org/dc/terms/description'
    >>> browser.getControl(name='form.buttons.save').click()

The Simple DMCC RDF Generator for organs is now ready.  We'll set it up as the
generator for our simple source::

    >>> source.generator = RelationValue(intIDs.getId(generator))
    >>> transaction.commit()
    >>> source.generator.to_object.title
    'Organs'
    >>> browser.open(portalURL + '/a-simple-source')
    >>> browser.contents
    '...Generator...href="http://nohost/plone/organs"...Organs...'

Tickling::

    >>> browser.open(portalURL + '/@@updateRDF')  # 4

And now::

    >>> browser.open(portalURL + '/a-simple-source/@@rdf')
    >>> browser.headers['content-type']
    'application/rdf+xml'
    >>> import rdflib
    >>> graph = rdflib.Graph()
    >>> graph.parse(data=browser.contents, format='xml')
    <Graph identifier=...(<class 'rdflib.graph.Graph'>)>
    >>> len(graph)
    68
    >>> namespaceURIs = [i[1] for i in graph.namespaces()]
    >>> namespaceURIs.sort()
    >>> namespaceURIs[0]
    rdflib.term.URIRef('http://purl.org/dc/terms/')
    >>> subjects = frozenset([str(i) for i in graph.subjects() if str(i)])
    >>> subjects = list(subjects)
    >>> subjects.sort()
    >>> subjects[0:3]
    ['urn:testing:data:organ:1', 'urn:testing:data:organ:10', 'urn:testing:data:organ:11']
    >>> predicates = frozenset([str(i) for i in graph.predicates()])
    >>> predicates = list(predicates)
    >>> predicates.sort()
    >>> predicates[0:2]
    ['http://purl.org/dc/terms/title', 'http://www.w3.org/1999/02/22-rdf-syntax-ns#type']
    >>> objects = [str(i) for i in graph.objects() if isinstance(i, rdflib.term.Literal)]
    >>> objects.sort()
    >>> objects[0:5]
    ['Bladder', 'Blood', 'Bone', 'Brain', 'Breast']

Now that's some fine looking RDF.


Empty Values
............

The DMCC's web services are "full" of "empty" information.  In our organ test
data, we reflect this in the entry for "Bone": it has an empty "Description"
field.  When a field like this is empty, the corresponding RDF graph should
not contain an empty statement about Bone's description.

Note::

    >>> results = graph.query('''select ?description where {
    ...    <urn:testing:data:organ:3> <http://purl.org/dc/terms/description> ?description .
    ... }''')
    >>> len(results)
    0

Looks good.


Reference Predicate Handlers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Diseases are another topic covered by the DMCC.  Diseases affect specific
organs, so they give us an opportunity to demonstrate Reference Predicate
Handlers.  First, we'll make a new Simple DMCC RDF Generator::

    >>> browser.open(portalURL)
    >>> browser.getLink(id='edrn-rdf-simpledmccrdfgenerator').click()
    >>> browser.getControl(name='form.widgets.title').value = 'Diseases'
    >>> browser.getControl(name='form.widgets.description').value = 'Generates lists of diseases.'
    >>> browser.getControl(name='form.widgets.webServiceURL').value = 'testscheme://localhost/ws_newcompass.asmx?WSDL'
    >>> browser.getControl(name='form.widgets.operationName').value = 'Disease'
    >>> browser.getControl(name='form.widgets.verificationNum').value = '0'
    >>> browser.getControl(name='form.widgets.uriPrefix').value = 'urn:testing:data:disease:'
    >>> browser.getControl(name='form.widgets.identifyingKey').value = 'Identifier'
    >>> browser.getControl(name='form.widgets.typeURI').value = 'urn:testing:types:disease'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> generator = portal['diseases']

Now a couple Literal Predicate Handler to handle the basics like title, etc.::

    >>> browser.open(portalURL + '/diseases')
    >>> browser.getLink(id='edrn-rdf-literalpredicatehandler').click()
    >>> browser.getControl(name='form.widgets.title').value = 'item_Title'
    >>> browser.getControl(name='form.widgets.description').value = 'Maps the <item_Title> key to the Dublin Core title predicate URI.'
    >>> browser.getControl(name='form.widgets.predicateURI').value = 'http://purl.org/dc/terms/title'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> browser.open(portalURL + '/diseases')
    >>> browser.getLink(id='edrn-rdf-literalpredicatehandler').click()
    >>> browser.getControl(name='form.widgets.title').value = 'icd9'
    >>> browser.getControl(name='form.widgets.description').value = 'Maps the <icd9> key to the an EDRN-specific URI.'
    >>> browser.getControl(name='form.widgets.predicateURI').value = 'urn:testing:predicates:icd9code'
    >>> browser.getControl(name='form.buttons.save').click()

Diseases affect organs, so here's the reference::

    >>> browser.open(portalURL + '/diseases')
    >>> l = browser.getLink(id='edrn-rdf-referencepredicatehandler')
    >>> l.url.endswith('++add++edrn.rdf.referencepredicatehandler')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = 'body_system'
    >>> browser.getControl(name='form.widgets.description').value = 'Maps to organs that diseases affect.'
    >>> browser.getControl(name='form.widgets.predicateURI').value = 'urn:testing:predicates:affectedOrgan'
    >>> browser.getControl(name='form.widgets.uriPrefix').value = 'urn:testing:data:organs:'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'body_system' in generator.keys()
    True
    >>> predicateHandler = generator['body_system']
    >>> predicateHandler.title
    'body_system'
    >>> predicateHandler.description
    'Maps to organs that diseases affect.'
    >>> predicateHandler.predicateURI
    'urn:testing:predicates:affectedOrgan'
    >>> predicateHandler.uriPrefix
    'urn:testing:data:organs:'

The Simple DMCC RDF Generator for diseases is now ready.  We'll set it up as
the generator for our simple source::

    >>> source.generator = RelationValue(intIDs.getId(generator))
    >>> transaction.commit()
    >>> source.generator.to_object.title
    'Diseases'

Tickling::

    >>> browser.open(portalURL + '/@@updateRDF')  # 5

And now::

    >>> browser.open(portalURL + '/a-simple-source/@@rdf')
    >>> graph = rdflib.Graph()
    >>> graph.parse(data=browser.contents, format='xml')
    <Graph identifier=...(<class 'rdflib.graph.Graph'>)>
    >>> len(graph)
    124
    >>> namespaceURIs = [i[1] for i in graph.namespaces()]
    >>> namespaceURIs.sort()
    >>> namespaceURIs[0]
    rdflib.term.URIRef('http://purl.org/dc/terms/')
    >>> namespaceURIs[-1]
    rdflib.term.URIRef('urn:testing:types:')
    >>> subjects = frozenset([str(i) for i in graph.subjects() if str(i)])
    >>> subjects = list(subjects)
    >>> subjects.sort()
    >>> subjects[0:3]
    ['urn:testing:data:disease:1', 'urn:testing:data:disease:10', 'urn:testing:data:disease:11']
    >>> predicates = frozenset([str(i) for i in graph.predicates()])
    >>> predicates = list(predicates)
    >>> predicates.sort()
    >>> predicates[0]
    'http://purl.org/dc/terms/title'
    >>> predicates[2]
    'urn:testing:predicates:affectedOrgan'
    >>> predicates[3]
    'urn:testing:predicates:icd9code'
    >>> objects = [str(i) for i in graph.objects() if isinstance(i, rdflib.term.Literal)]
    >>> objects.sort()
    >>> objects[27:32]
    ['205', '208.9', 'Liver cell carcinoma', 'Lymphoid leukaemia', 'Malignant melanoma of skin']
    >>> references = frozenset([str(i) for i in graph.objects() if isinstance(i, rdflib.term.URIRef)])
    >>> references = list(references)
    >>> references.sort()
    >>> references[0:3]
    ['urn:testing:data:organs:1', 'urn:testing:data:organs:10', 'urn:testing:data:organs:11']

That's even better lookin' RDF.


Multiple Literal Values
~~~~~~~~~~~~~~~~~~~~~~~

Some of the information in the DMCC's web service contains literal values that
are separated by commas.  For example, the ``Publication`` operation yields a
sequence of comma-separated author names.  In RDF, we don't use such in-band
signaling, since that's moronic.  Instead, we make multiple statements about a
publication, each one describing a separate author.

We've got a class to handle just that case: the Multi-Literal Predicate
Handler.

Let's try it out.  First, let's make a brand new Simple DMCC RDF Generator for
publications:

    >>> browser.open(portalURL)
    >>> browser.getLink(id='edrn-rdf-simpledmccrdfgenerator').click()
    >>> browser.getControl(name='form.widgets.title').value = 'Publications'
    >>> browser.getControl(name='form.widgets.description').value = 'Generates lists of journal articles and stuff.'
    >>> browser.getControl(name='form.widgets.webServiceURL').value = 'testscheme://localhost/ws_newcompass.asmx?WSDL'
    >>> browser.getControl(name='form.widgets.operationName').value = 'Publication'
    >>> browser.getControl(name='form.widgets.verificationNum').value = '0'
    >>> browser.getControl(name='form.widgets.uriPrefix').value = 'urn:testing:data:publication:'
    >>> browser.getControl(name='form.widgets.identifyingKey').value = 'Identifier'
    >>> browser.getControl(name='form.widgets.typeURI').value = 'urn:testing:types:publication'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> generator = portal['publications']

Now a Literal Predicate Handler to handle the title of each publication::

    >>> browser.open(portalURL + '/publications')
    >>> browser.getLink(id='edrn-rdf-literalpredicatehandler').click()
    >>> browser.getControl(name='form.widgets.title').value = 'item_Title'
    >>> browser.getControl(name='form.widgets.description').value = 'Maps the <item_Title> key to the Dublin Core title predicate URI.'
    >>> browser.getControl(name='form.widgets.predicateURI').value = 'http://purl.org/dc/terms/title'
    >>> browser.getControl(name='form.buttons.save').click()

And a Multi-Literal Predicate Handler for the authors::

    >>> browser.open(portalURL + '/publications')
    >>> l = browser.getLink(id='edrn-rdf-multiliteralpredicatehandler')
    >>> l.url.endswith('++add++edrn.rdf.multiliteralpredicatehandler')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = 'Author'
    >>> browser.getControl(name='form.widgets.description').value = 'Maps to authors of publications.'
    >>> browser.getControl(name='form.widgets.predicateURI').value = 'http://purl.org/dc/terms/creator'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'author' in generator.keys()
    True
    >>> predicateHandler = generator['author']
    >>> predicateHandler.title
    'Author'
    >>> predicateHandler.description
    'Maps to authors of publications.'
    >>> predicateHandler.predicateURI
    'http://purl.org/dc/terms/creator'

Does it work?  Let's make the simple source use it to find out::

    >>> source.generator = RelationValue(intIDs.getId(generator))
    >>> transaction.commit()
    >>> source.generator.to_object.title
    'Publications'

Tickling::

    >>> browser.open(portalURL + '/@@updateRDF')  # 6

And now for the RDF::

    >>> browser.open(portalURL + '/a-simple-source/@@rdf')
    >>> graph = rdflib.Graph()
    >>> graph.parse(data=browser.contents, format='xml')
    <Graph identifier=...(<class 'rdflib.graph.Graph'>)>
    >>> len(graph)
    31809
    >>> subjects = frozenset([str(i) for i in graph.subjects() if str(i)])
    >>> subjects = list(subjects)
    >>> subjects.sort()
    >>> subjects[0:3]
    ['urn:testing:data:publication:1001', 'urn:testing:data:publication:1002', 'urn:testing:data:publication:1003']
    >>> predicates = frozenset([str(i) for i in graph.predicates()])
    >>> predicates = list(predicates)
    >>> predicates.sort()
    >>> predicates[0]
    'http://purl.org/dc/terms/creator'
    >>> objects = [str(i) for i in graph.objects() if isinstance(i, rdflib.term.Literal)]
    >>> objects.sort()
    >>> objects[40:43]
    ['A Pan-Cancer Analysis of Enhancer Expression in Nearly 9000 Patient Samples', 'A Panel of Novel Detection and Prognostic Methylated DNA Markers in Primary Non-Small Cell Lung Cancer and Serum DNA', 'A Plasma Biomarker Panel to Identify Surgically Resectable Early-Stage Pancreatic Cancer']

Yes, fine—and I mean *fiiiiiine*—RDF.


Advanced RDF Generators
=======================

The Simple DMCC RDF Generator handles simple statements with literal objects
as well as referential statements with reference objects.  With this, we can
provide RDF for a number of the DMCC's sources of EDRN information, including:

• Body systems
• Diseases
• Sites
• Publications
• Registered Persons

More tricky are EDRN's committees and protocols.  They're so tricky, in fact,
that they have dedicated RDF generators:

• DMCC Committee RDF Generator
• DMCC Protocols RDF Generator

Let's dive right in.


Generating RDF for Committees
-----------------------------

Committees require input from multiple SOAP API calls into the DMCC's ungainly
web service.  They may be created anywhere::

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='edrn-rdf-dmcccommitteerdfgenerator')
    >>> l.url.endswith('++add++edrn.rdf.dmcccommitteerdfgenerator')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = 'Committees'
    >>> browser.getControl(name='form.widgets.description').value = 'Generates info about EDRN committees.'
    >>> browser.getControl(name='form.widgets.webServiceURL').value = 'testscheme://localhost/ws_newcompass.asmx?WSDL'
    >>> browser.getControl(name='form.widgets.committeeOperation').value = 'Committees'
    >>> browser.getControl(name='form.widgets.membershipOperation').value = 'Committee_Membership'
    >>> browser.getControl(name='form.widgets.verificationNum').value = '0'
    >>> browser.getControl(name='form.widgets.typeURI').value = 'urn:testing:types:committee'
    >>> browser.getControl(name='form.widgets.uriPrefix').value = 'urn:testing:data:committee:'
    >>> browser.getControl(name='form.widgets.personPrefix').value = 'urn:testing:data:person:'
    >>> browser.getControl(name='form.widgets.titlePredicateURI').value = 'http://purl.org/dc/terms/title'
    >>> browser.getControl(name='form.widgets.abbrevNamePredicateURI').value = 'urn:testing:predicates:abbrevName'
    >>> browser.getControl(name='form.widgets.committeeTypePredicateURI').value = 'urn:testing:predicates:committeeType'
    >>> browser.getControl(name='form.widgets.chairPredicateURI').value = 'urn:testing:predicates:chair'
    >>> browser.getControl(name='form.widgets.coChairPredicateURI').value = 'urn:testing:predicates:coChair'
    >>> browser.getControl(name='form.widgets.consultantPredicateURI').value = 'urn:testing:predicates:consultant'
    >>> browser.getControl(name='form.widgets.memberPredicateURI').value = 'urn:testing:predicates:member'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'committees' in portal.keys()
    True
    >>> generator = portal['committees']
    >>> generator.title
    'Committees'
    >>> generator.description
    'Generates info about EDRN committees.'
    >>> generator.webServiceURL
    'testscheme://localhost/ws_newcompass.asmx?WSDL'
    >>> generator.committeeOperation
    'Committees'
    >>> generator.membershipOperation
    'Committee_Membership'
    >>> generator.verificationNum
    '0'
    >>> generator.typeURI
    'urn:testing:types:committee'
    >>> generator.uriPrefix
    'urn:testing:data:committee:'
    >>> generator.personPrefix
    'urn:testing:data:person:'
    >>> generator.titlePredicateURI
    'http://purl.org/dc/terms/title'
    >>> generator.abbrevNamePredicateURI
    'urn:testing:predicates:abbrevName'
    >>> generator.committeeTypePredicateURI
    'urn:testing:predicates:committeeType'
    >>> generator.chairPredicateURI
    'urn:testing:predicates:chair'
    >>> generator.coChairPredicateURI
    'urn:testing:predicates:coChair'
    >>> generator.consultantPredicateURI
    'urn:testing:predicates:consultant'
    >>> generator.memberPredicateURI
    'urn:testing:predicates:member'

Looks good.  Now, we could make this generator be the source for our simple
source that we've been using so far, but frankly, we've been riding the simple
source pretty hard for a while now.  Let's give it a rest and come up with a
fresh source, just for the committees generator::

    >>> browser.open(portalURL)
    >>> browser.getLink(id='edrn-rdf-rdfsource').click()
    >>> browser.getControl(name='form.widgets.title').value = 'A Committee Source'
    >>> browser.getControl(name='form.widgets.description').value = "It's just for functional tests."
    >>> browser.getControl(name='form.widgets.active:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> source = portal['a-committee-source']
    >>> source.generator = RelationValue(intIDs.getId(generator))
    >>> transaction.commit()

Now for the tickle::

    >>> browser.open(portalURL + '/@@updateRDF')  # 7

And now for the RDF::

    >>> browser.open(portalURL + '/a-committee-source/@@rdf')
    >>> graph = rdflib.Graph()
    >>> graph.parse(data=browser.contents, format='xml')
    <Graph identifier=...(<class 'rdflib.graph.Graph'>)>
    >>> len(graph)
    298
    >>> subjects = frozenset([str(i) for i in graph.subjects() if str(i)])
    >>> subjects = list(subjects)
    >>> subjects.sort()
    >>> subjects[0:3]
    ['urn:testing:data:committee:1', 'urn:testing:data:committee:10', 'urn:testing:data:committee:14']
    >>> predicates = frozenset([str(i) for i in graph.predicates()])
    >>> predicates = list(predicates)
    >>> predicates.sort()
    >>> predicates[0]
    'http://purl.org/dc/terms/title'
    >>> predicates[2]
    'urn:testing:predicates:abbrevName'
    >>> predicates[3]
    'urn:testing:predicates:chair'
    >>> predicates[4]
    'urn:testing:predicates:coChair'
    >>> predicates[5]
    'urn:testing:predicates:committeeType'
    >>> predicates[6]
    'urn:testing:predicates:consultant'
    >>> predicates[7]
    'urn:testing:predicates:member'
    >>> objects = [str(i) for i in graph.objects() if isinstance(i, rdflib.term.Literal)]
    >>> objects.sort()
    >>> objects[0:6]
    ['Assoc. Member', 'Associate Member', 'BDL', 'BRL', 'Biomarker Developmental  Laboratories', 'Biomarker Reference Laboratories']

Major wootness.


Generating RDF for Protocols
----------------------------

Protocols are quite a bit tricky.  Generators for them may be created
anywhere::

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='edrn-rdf-dmccprotocolrdfgenerator')
    >>> l.url.endswith('++add++edrn.rdf.dmccprotocolrdfgenerator')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = 'Protocols'
    >>> browser.getControl(name='form.widgets.description').value = 'Generates info about EDRN protocols.'
    >>> browser.getControl(name='form.widgets.webServiceURL').value = 'testscheme://localhost/ws_newcompass.asmx?WSDL'
    >>> browser.getControl(name='form.widgets.protocolOrStudyOperation').value = 'Protocol_or_Study'
    >>> browser.getControl(name='form.widgets.edrnProtocolOperation').value = 'EDRN_Protocol'
    >>> browser.getControl(name='form.widgets.protoSiteSpecificsOperation').value = 'Protocol_Site_Specifics'
    >>> browser.getControl(name='form.widgets.protoProtoRelationshipOperation').value = 'Protocol_Protocol_Relationship'
    >>> browser.getControl(name='form.widgets.verificationNum').value = '0'
    >>> browser.getControl(name='form.widgets.typeURI').value = 'urn:testing:types:protocol'
    >>> browser.getControl(name='form.widgets.siteSpecificTypeURI').value = 'urn:testing:types:protocol:sitespecific'
    >>> browser.getControl(name='form.widgets.uriPrefix').value = 'urn:testing:data:protocol:'
    >>> browser.getControl(name='form.widgets.siteSpecURIPrefix').value = 'urn:testing:data:protocol:site-spec:'
    >>> browser.getControl(name='form.widgets.publicationURIPrefix').value = 'urn:testing:data:publication:'
    >>> browser.getControl(name='form.widgets.siteURIPrefix').value = 'urn:testing:data:sites:'
    >>> browser.getControl(name='form.widgets.titleURI').value = 'urn:testing:predicates:titleURI'
    >>> browser.getControl(name='form.widgets.abstractURI').value = 'urn:testing:predicates:abstractURI'
    >>> browser.getControl(name='form.widgets.involvedInvestigatorSiteURI').value = 'urn:testing:predicates:involvedInvestigatorSiteURI'
    >>> browser.getControl(name='form.widgets.bmNameURI').value = 'urn:testing:predicates:bmNameURI'
    >>> browser.getControl(name='form.widgets.coordinateInvestigatorSiteURI').value = 'urn:testing:predicates:coordinateInvestigatorSiteURI'
    >>> browser.getControl(name='form.widgets.leadInvestigatorSiteURI').value = 'urn:testing:predicates:leadInvestigatorSiteURI'
    >>> browser.getControl(name='form.widgets.collaborativeGroupTextURI').value = 'urn:testing:predicates:collaborativeGroupTextURI'
    >>> browser.getControl(name='form.widgets.phasedStatusURI').value = 'urn:testing:predicates:phasedStatusURI'
    >>> browser.getControl(name='form.widgets.aimsURI').value = 'urn:testing:predicates:aimsURI'
    >>> browser.getControl(name='form.widgets.analyticMethodURI').value = 'urn:testing:predicates:analyticMethodURI'
    >>> browser.getControl(name='form.widgets.blindingURI').value = 'urn:testing:predicates:blindingURI'
    >>> browser.getControl(name='form.widgets.cancerTypeURI').value = 'urn:testing:predicates:cancerTypeURI'
    >>> browser.getControl(name='form.widgets.commentsURI').value = 'urn:testing:predicates:commentsURI'
    >>> browser.getControl(name='form.widgets.dataSharingPlanURI').value = 'urn:testing:predicates:dataSharingPlanURI'
    >>> browser.getControl(name='form.widgets.inSituDataSharingPlanURI').value = 'urn:testing:predicates:inSituDataSharingPlanURI'
    >>> browser.getControl(name='form.widgets.finishDateURI').value = 'urn:testing:predicates:finishDateURI'
    >>> browser.getControl(name='form.widgets.estimatedFinishDateURI').value = 'urn:testing:predicates:estimatedFinishDateURI'
    >>> browser.getControl(name='form.widgets.startDateURI').value = 'urn:testing:predicates:startDateURI'
    >>> browser.getControl(name='form.widgets.designURI').value = 'urn:testing:predicates:designURI'
    >>> browser.getControl(name='form.widgets.fieldOfResearchURI').value = 'urn:testing:predicates:fieldOfResearchURI'
    >>> browser.getControl(name='form.widgets.abbreviatedNameURI').value = 'urn:testing:predicates:abbreviatedNameURI'
    >>> browser.getControl(name='form.widgets.objectiveURI').value = 'urn:testing:predicates:objectiveURI'
    >>> browser.getControl(name='form.widgets.projectFlagURI').value = 'urn:testing:predicates:projectFlagURI'
    >>> browser.getControl(name='form.widgets.protocolTypeURI').value = 'urn:testing:predicates:protocolTypeURI'
    >>> browser.getControl(name='form.widgets.publicationsURI').value = 'urn:testing:predicates:publicationsURI'
    >>> browser.getControl(name='form.widgets.outcomeURI').value = 'urn:testing:predicates:outcomeURI'
    >>> browser.getControl(name='form.widgets.secureOutcomeURI').value = 'urn:testing:predicates:secureOutcomeURI'
    >>> browser.getControl(name='form.widgets.finalSampleSizeURI').value = 'urn:testing:predicates:finalSampleSizeURI'
    >>> browser.getControl(name='form.widgets.plannedSampleSizeURI').value = 'urn:testing:predicates:plannedSampleSizeURI'
    >>> browser.getControl(name='form.widgets.isAPilotForURI').value = 'urn:testing:predicates:isAPilotForURI'
    >>> browser.getControl(name='form.widgets.obtainsDataFromURI').value = 'urn:testing:predicates:obtainsDataFromURI'
    >>> browser.getControl(name='form.widgets.providesDataToURI').value = 'urn:testing:predicates:providesDataToURI'
    >>> browser.getControl(name='form.widgets.contributesSpecimensURI').value = 'urn:testing:predicates:contributesSpecimensURI'
    >>> browser.getControl(name='form.widgets.obtainsSpecimensFromURI').value = 'urn:testing:predicates:obtainsSpecimensFromURI'
    >>> browser.getControl(name='form.widgets.hasOtherRelationshipURI').value = 'urn:testing:predicates:hasOtherRelationshipURI'
    >>> browser.getControl(name='form.widgets.animalSubjectTrainingReceivedURI').value = 'urn:testing:predicates:animalSubjectTrainingReceivedURI'
    >>> browser.getControl(name='form.widgets.humanSubjectTrainingReceivedURI').value = 'urn:testing:predicates:humanSubjectTrainingReceivedURI'
    >>> browser.getControl(name='form.widgets.irbApprovalNeededURI').value = 'urn:testing:predicates:irbApprovalNeededURI'
    >>> browser.getControl(name='form.widgets.currentIRBApprovalDateURI').value = 'urn:testing:predicates:currentIRBApprovalDateURI'
    >>> browser.getControl(name='form.widgets.originalIRBApprovalDateURI').value = 'urn:testing:predicates:originalIRBApprovalDateURI'
    >>> browser.getControl(name='form.widgets.irbExpirationDateURI').value = 'urn:testing:predicates:irbExpirationDateURI'
    >>> browser.getControl(name='form.widgets.generalIRBNotesURI').value = 'urn:testing:predicates:generalIRBNotesURI'
    >>> browser.getControl(name='form.widgets.irbNumberURI').value = 'urn:testing:predicates:irbNumberURI'
    >>> browser.getControl(name='form.widgets.siteRoleURI').value = 'urn:testing:predicates:siteRoleURI'
    >>> browser.getControl(name='form.widgets.reportingStageURI').value = 'urn:testing:predicates:reportingStageURI'
    >>> browser.getControl(name='form.widgets.eligibilityCriteriaURI').value = 'urn:testing:predicates:eligibilityCriteriaURI'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'protocols' in portal.keys()
    True
    >>> generator = portal['protocols']

We won't bother confirming that every field got its correct value;
plone.app.dexterity had better damn well take care of that for us.  Instead,
let's make a source to hold graphs generated by this protocol generator::

    >>> browser.open(portalURL)
    >>> browser.getLink(id='edrn-rdf-rdfsource').click()
    >>> browser.getControl(name='form.widgets.title').value = 'A Protocol Source'
    >>> browser.getControl(name='form.widgets.description').value = "It's just for functional tests."
    >>> browser.getControl(name='form.widgets.active:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> source = portal['a-protocol-source']
    >>> source.generator = RelationValue(intIDs.getId(generator))
    >>> transaction.commit()

Once again, tickling::

    >>> browser.open(portalURL + '/@@updateRDF')  # 8

And now for the RDF::

    >>> browser.open(portalURL + '/a-protocol-source/@@rdf')
    >>> graph = rdflib.Graph()
    >>> graph.parse(data=browser.contents, format='xml')
    <Graph identifier=...(<class 'rdflib.graph.Graph'>)>
    >>> len(graph) > 9422
    True
    >>> subjects = frozenset([str(i) for i in graph.subjects() if str(i)])
    >>> subjects = list(subjects)
    >>> subjects.sort()
    >>> subjects[0]
    'urn:testing:data:protocol:0'
    >>> predicates = frozenset([str(i) for i in graph.predicates()])
    >>> predicates = list(predicates)
    >>> predicates.sort()
    >>> predicates[1]
    'urn:testing:predicates:abbreviatedNameURI'
    >>> objects = [str(i) for i in graph.objects() if isinstance(i, rdflib.term.Literal)]
    >>> objects.sort()
    >>> objects[-2]
    '~400'


LabCAS Collections
==================

Science data collections in LabCAS don't come from the DMCC but for some
reason we handle them here as well. All right, let's make a LabCAS source and
generator. First, the generator::

    >>> from z3c.relationfield import RelationValue
    >>> from zope.app.intid.interfaces import IIntIds
    >>> from zope.component import getUtility
    >>> intIDs = getUtility(IIntIds)
    >>> import transaction
    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='edrn-rdf-labcascollectionrdfgenerator')
    >>> l.url.endswith('++add++edrn.rdf.labcascollectionrdfgenerator')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = 'LabCAS Generator'
    >>> browser.getControl(name='form.widgets.description').value = 'A LabCAS RDF generator for testing.'
    >>> import pkg_resources
    >>> import edrn.rdf.tests
    >>> solrTestData = pkg_resources.resource_filename(edrn.rdf.tests.__name__, 'tests/testdata/labcas-solr.json')
    >>> browser.getControl(name='form.widgets.labcasSolrURL').value = 'file:' + solrTestData
    >>> browser.getControl(name='form.widgets.username').value = 'service'
    >>> browser.getControl(name='form.widgets.password').value = 'secret'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> browser.open(portalURL)
    >>> 'labcas-generator' in portal.keys()
    True
    >>> generator = portal['labcas-generator']
    >>> generator.labcasSolrURL.startswith('file:/')
    True
    >>> generator.labcasSolrURL.endswith('/labcas-solr.json')
    True
    >>> generator.username
    'service'
    >>> generator.password
    'secret'

And now its source::

    >>> browser.open(portalURL)
    >>> browser.getLink(id='edrn-rdf-rdfsource').click()
    >>> browser.getControl(name='form.widgets.title').value = 'LabCAS Source'
    >>> browser.getControl(name='form.widgets.description').value = "It's just for functional tests."
    >>> browser.getControl(name='form.widgets.active:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> source = portal['labcas-source']
    >>> source.generator = RelationValue(intIDs.getId(generator))
    >>> transaction.commit()
    >>> source.title
    'LabCAS Source'
    >>> source.generator.to_object.title
    'LabCAS Generator'
    >>> source.active
    True

At this point, we'd make RDF and see if it looks right with something like::

    .. >>> browser.open(portalURL + '/@@updateRDF')  # 9
    .. >>> browser.open(portalURL + '/labcas-source/@@rdf')
    .. >>> browser.isHtml
    .. False
    .. >>> browser.headers['content-type']
    .. 'application/rdf+xml'
    .. >>> browser.contents
    .. b'<?xml version="1.0" encoding="utf-8"?>\n<rdf:RDF\n  xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"\/>many statements</rdf:RDF>\n'

Except ``pysolr`` uses ``requests`` which doesn't provide an easy way of
inserting our own ``testscheme:`` URL handler and doesn't even handle
``file:`` URLs. So screw it.


RDF Generators added by David
=============================

Generating RDF for Biomuta
--------------------------

Biomuta generator grabs csv file from George Washington University's 
High-performance Integrated Virtual Environment (HIVE).  They may be created anywhere::

    >>> browser.open(portalURL)
    >>> l = browser.getLink(id='edrn-rdf-biomutardfgenerator')
    >>> l.url.endswith('++add++edrn.rdf.biomutardfgenerator')
    True
    >>> l.click()
    >>> browser.getControl(name='form.widgets.title').value = 'Biomuta'
    >>> browser.getControl(name='form.widgets.description').value = 'Generates mutation info about EDRN biomarkers.'
    >>> browser.getControl(name='form.widgets.webServiceURL').value = 'testscheme://localhost/biomuta.tsv'
    >>> browser.getControl(name='form.widgets.typeURI').value = 'urn:testing:types:biomuta'
    >>> browser.getControl(name='form.widgets.uriPrefix').value = 'urn:testing:data:biomuta:'
    >>> browser.getControl(name='form.widgets.geneNamePredicateURI').value = 'urn:testing:predicates:geneName'
    >>> browser.getControl(name='form.widgets.uniProtACPredicateURI').value = 'urn:testing:predicates:uniprotAccession'
    >>> browser.getControl(name='form.widgets.mutCountPredicateURI').value = 'urn:testing:predicates:mutationCount'
    >>> browser.getControl(name='form.widgets.pmidCountPredicateURI').value = 'urn:testing:predicates:pubmedIDCount'
    >>> browser.getControl(name='form.widgets.cancerDOCountPredicateURI').value = 'urn:testing:predicates:cancerDOCount'
    >>> browser.getControl(name='form.widgets.affProtFuncSiteCountPredicateURI').value = 'urn:testing:predicates:affectedProtFuncSiteCount'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'biomuta' in portal.keys()
    True
    >>> generator = portal['biomuta']
    >>> generator.title
    'Biomuta'
    >>> generator.description
    'Generates mutation info about EDRN biomarkers.'
    >>> generator.webServiceURL
    'testscheme://localhost/biomuta.tsv'
    >>> generator.typeURI
    'urn:testing:types:biomuta'
    >>> generator.uriPrefix
    'urn:testing:data:biomuta:'
    >>> generator.geneNamePredicateURI
    'urn:testing:predicates:geneName'
    >>> generator.uniProtACPredicateURI
    'urn:testing:predicates:uniprotAccession'
    >>> generator.mutCountPredicateURI
    'urn:testing:predicates:mutationCount'
    >>> generator.pmidCountPredicateURI
    'urn:testing:predicates:pubmedIDCount'
    >>> generator.cancerDOCountPredicateURI
    'urn:testing:predicates:cancerDOCount'
    >>> generator.affProtFuncSiteCountPredicateURI
    'urn:testing:predicates:affectedProtFuncSiteCount'

Looks good.  Fresh source for the biomuta generator::

    >>> browser.open(portalURL)
    >>> browser.getLink(id='edrn-rdf-rdfsource').click()
    >>> browser.getControl(name='form.widgets.title').value = 'A Biomuta Source'
    >>> browser.getControl(name='form.widgets.description').value = "It's just for functional tests."
    >>> browser.getControl(name='form.widgets.active:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> source = portal['a-biomuta-source']
    >>> source.generator = RelationValue(intIDs.getId(generator))
    >>> transaction.commit()

Now for the tickle::

    >>> browser.open(portalURL + '/@@updateRDF')  # 10

And now for the RDF::

    >>> browser.open(portalURL + '/a-biomuta-source/@@rdf')
    >>> graph = rdflib.Graph()
    >>> graph.parse(data=browser.contents, format='xml')
    <Graph identifier=...(<class 'rdflib.graph.Graph'>)>
    >>> len(graph)
    131187
    >>> subjects = frozenset([str(i) for i in graph.subjects() if str(i)])
    >>> subjects = list(subjects)
    >>> subjects.sort()
    >>> subjects[0:3]
    ['urn:testing:data:biomuta:02/14/02', 'urn:testing:data:biomuta:A1BG', 'urn:testing:data:biomuta:A1CF']
    >>> predicates = frozenset([str(i) for i in graph.predicates()])
    >>> predicates = list(predicates)
    >>> predicates.sort()
    >>> predicates[1]
    'urn:testing:predicates:affectedProtFuncSiteCount'
    >>> predicates[2]
    'urn:testing:predicates:cancerDOCount'
    >>> predicates[3]
    'urn:testing:predicates:geneName'
    >>> predicates[4]
    'urn:testing:predicates:mutationCount'
    >>> predicates[5]
    'urn:testing:predicates:pubmedIDCount'
    >>> predicates[6]
    'urn:testing:predicates:uniprotAccession'
    >>> objects = [str(i) for i in graph.objects() if isinstance(i, rdflib.term.Literal)]
    >>> objects.sort()
    >>> objects[0:6]
    ['0', '0', '0', '0', '0', '0']

Woot Woot.


Culling Old Files
=================

One problem we've had with long-term running of this is that as data changes
we keep old copies of RDF data in case we ever need to revert. (This has never
happened in practice yet.) But those old RDF files build up. At one point, the
database was 32 GiB! So let's address
https://github.com/EDRN/CancerDataExpo/issues/6 by  creating a new RDF
generator, one specially designed so that it always makes changing graphs of
statements. Our approach will be to run the generator multiple times and see
how many files we get, hoping there's a limit.

However, since we can't run just one generator, let's first disable all the
ones we've built up so far::

    >>> import plone.api
    >>> catalog = plone.api.portal.get_tool('portal_catalog')
    >>> from edrn.rdf.rdfsource import IRDFSource
    >>> results = catalog(object_provides=IRDFSource.__identifier__)
    >>> for brain in results:
    ...     source = brain.getObject()
    ...     source.active = False
    >>> transaction.commit()

Now, here's the always-mutating generator::

    >>> browser.open(portalURL)
    >>> browser.getLink(id='edrn-rdf-mutatingrdfgenerator').click()
    >>> browser.getControl(name='form.widgets.title').value = 'Mutating RDF'
    >>> browser.getControl(name='form.widgets.description').value = 'Generates ever-changing graphs.'
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'mutating-rdf' in portal.keys()
    True
    >>> generator = portal['mutating-rdf']

And a single, new RDF source::

    >>> browser.open(portalURL)
    >>> browser.getLink(id='edrn-rdf-rdfsource').click()
    >>> browser.getControl(name='form.widgets.title').value = 'A Growing Source'
    >>> browser.getControl(name='form.widgets.description').value = "It's just for functional tests."
    >>> browser.getControl(name='form.widgets.active:list').value = True
    >>> browser.getControl(name='form.buttons.save').click()
    >>> 'a-growing-source' in portal.keys()
    True
    >>> source = portal['a-growing-source']

Connecting them::

    >>> source.generator = RelationValue(intIDs.getId(generator))
    >>> transaction.commit()
    >>> source.generator.to_object.title
    'Mutating RDF'

And confirming we have no files to start::

    >>> len(source.keys())
    0

Okay, so we'll generate our first file::

    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    1

And generate 15 more:

    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    2
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    3
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    4
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    5
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    6
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    7
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    8
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    9
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    10
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    11
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    12
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    13
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    14
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    15
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    16

But now the system should trim the eldest::

    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    16

No matter how many more times we generate RDF::

    >>> browser.open(portalURL + '/@@updateRDF')
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> browser.open(portalURL + '/@@updateRDF')
    >>> len(source.keys())
    16

Whew.

