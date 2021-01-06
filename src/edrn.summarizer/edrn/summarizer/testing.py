# encoding: utf-8
# Copyright 2011 California Institute of Technology. ALL RIGHTS
# RESERVED. U.S. Government Sponsorship acknowledged.

from plone.app.testing import PloneSandboxLayer, IntegrationTesting, FunctionalTesting, PLONE_FIXTURE
from plone.testing import z2
from suds.transport.http import HttpTransport
from suds.cache import ObjectCache
import pkg_resources, urllib, http


class TestSchemeHandler(urllib.request.BaseHandler):
    '''A special URL handler for the testing-only scheme ``testscheme``.'''
    def testscheme_open(self, req):
        try:
            selector = req.get_selector()
            if selector == '/ws_newcompass.asmx?WSDL':
                return urllib.response.addinfourl(
                    pkg_resources.resource_stream(__name__, 'tests/testdata/wsdl.xml'),
                    http.client.HTTPMessage(open('/dev/null')),
                    req.get_full_url(),
                    200
                )
            elif selector == '/ws_newcompass.asmx':
                soapResponse = urllib.parse.urlparse(req.get_header('Soapaction')).path.strip('"').split('/')[-1] + '.xml'
                return urllib.response.addinfourl(
                    pkg_resources.resource_stream(__name__, 'tests/testdata/' + soapResponse),
                    http.client.HTTPMessage(open('/dev/null')),
                    req.get_full_url(),
                    200
                )
            elif selector == '/biomuta.tsv':
                return urllib.response.addinfourl(
                    pkg_resources.resource_stream(__name__, 'tests/testdata/Biomuta.tsv'),
                    http.client.HTTPMessage(open('/dev/null')),
                    req.get_full_url(),
                    200
                )
            else:
                raise urllib.error.URLError('Not found')
        except Exception:
            raise urllib.error.URLError('Not found')


def monkeyedU2handlers(self):
    handlers = []
    handlers.append(TestSchemeHandler)
    handlers.append(urllib.request.ProxyHandler(self.proxy))
    return handlers


def monkeyedObjectCacheGetter(self, id):
    return None


class EDRN_Summarizer_Layer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)
    def setUpZope(self, app, configurationContext):
        import edrn.summarizer
        self.loadZCML(package=edrn.summarizer)
        urllib.request.install_opener(urllib.request.build_opener(TestSchemeHandler))
        # suds doesn't use the global openers, so monkey-patch it to include our testscheme handler
        HttpTransport.u2handlers = monkeyedU2handlers
        # don't let suds cache anything in /tmp
        ObjectCache.get = monkeyedObjectCacheGetter
    def setUpPloneSite(self, portal):
        self.applyProfile(portal, 'edrn.summarizer:default')
    def tearDownZope(self, app):
        z2.uninstallProduct(app, 'edrn.summarizer')


EDRN_SUMMARIZER = EDRN_Summarizer_Layer()
EDRN_SUMMARIZER_INTEGRATION_TESTING = IntegrationTesting(
    bases=(EDRN_SUMMARIZER,),
    name='EDRN_Summarizer_Layer:Integration'
)
EDRN_SUMMARIZER_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(EDRN_SUMMARIZER,),
    name='EDRN_SUMMARIZER_Layer:Functional'
)

# DEBUG:suds.client:sending to (https://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx)
# message:
# <?xml version="1.0" encoding="UTF-8"?>
# <SOAP-ENV:Envelope xmlns:ns0="http://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/">
#    <SOAP-ENV:Header/>
#    <ns1:Body>
#       <ns0:Body_System>
#          <ns0:verificationNum>0</ns0:verificationNum>
#       </ns0:Body_System>
#    </ns1:Body>
# </SOAP-ENV:Envelope>
# DEBUG:suds.client:headers = {'SOAPAction': '"http://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx/Body_System"', 'Content-Type': 'text/xml; charset=utf-8'}
# DEBUG:suds.transport.http:sending:
# URL:https://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx
# HEADERS: {'SOAPAction': '"http://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx/Body_System"', 'Content-Type': 'text/xml; charset=utf-8', 'Content-type': 'text/xml; charset=utf-8', 'Soapaction': '"http://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx/Body_System"'}
# MESSAGE:
# <?xml version="1.0" encoding="UTF-8"?><SOAP-ENV:Envelope xmlns:ns0="http://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx" xmlns:ns1="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"><SOAP-ENV:Header/><ns1:Body><ns0:Body_System><ns0:verificationNum>0</ns0:verificationNum></ns0:Body_System></ns1:Body></SOAP-ENV:Envelope>
# DEBUG:suds.transport.http:received:
# CODE: 200
# HEADERS: {'content-length': '4149', 'x-powered-by': 'ASP.NET', 'x-aspnet-version': '2.0.50727', 'server': 'Microsoft-IIS/6.0', 'connection': 'close', 'cache-control': 'private, max-age=0', 'date': 'Sat, 18 Aug 2012 13:40:06 GMT', 'content-type': 'text/xml; charset=utf-8'}
