# encoding: utf-8

'''Notifications.'''

from plone.registry.interfaces import IRegistry
from zope.component import getUtility
import plone.api, logging


_logger = logging.getLogger(__name__)
_body = 'Some errors occurred during RDF update:'


def notify_update_failures(context, failures):
    '''Let people who need to know about the update ``failures`` know about them.'''

    num_failures = len(failures)
    if num_failures <= 0: return

    registry = getUtility(IRegistry)
    targets = [i.split() for i in registry['edrn.rdf.notification.email'].split(',')]
    if len(targets) <= 0:
        _logger.warning('No email addresses configured to receive RDF update failures!')
        return

    mail_host, mfrom = plone.api.portal.get_tool('MailHost'), registry['plone.email_from_address']
    body = _body + '\n\n'
    for index, failure in zip(range(len(failures)), failures):
        body += f'№ {index + 1}. {failure["title"]} at {failure["url"]}:\n\n{failure["message"]}\n\n\n'

    # Zope MailHost allegedly handles strings but has trouble with non-ascii chars
    body = body.encode('ascii', 'backslashreplace').decode('utf-8')

    for target in targets:
        mail_host.simple_send(mto=target, mfrom=mfrom, subject='RDF update failures', body=body, immediate=True)
