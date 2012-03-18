**************
 DMCC Backend
**************

This is the backend information management and connection protocol system that
maintains data gathered from the Data Management & Coordinating Center
(DMCC_).  The DMCC provides web services and database access for information
vital to the Early Detection Research Network (EDRN_).  The Informatics Center
(IC_) uses that data to implement informatics services for EDRN.

These services include:

* Directory lookup backend for EDRN members via LDAP
* EDRN knowledge environment information via RDF

In the future, these services will include:

* TBD.

The remainder of this document tells how to set up this software.


Requirements
============

This software requires Python_ 2.6.  On the host cancer.jpl.nasa.gov, a
compatible Python is available in /usr/local/python/parts/opt/bin/python2.6.
Or you can use a compatible virtualenv_.

Don't put Varnish in front of Apache in front of the Zope instance in this
configuration.  Some RDF requests take longer than 5 minutes, and Varnish will
punt on them.


Deployment
==========

To deploy this software, do the following:

1. Extract it to a convenient location, say /usr/local/dmcc-backend.
2. Change the current working directory to that location.
3. Bootstrap it: ``python2.6 bootstrap.py -d``
4. Build it: ``bin/buildout``
5. Install the init script:
   ``install -o root -g root -m 755 bin/dmcc-backend /etc/init.d``
6. Add to chkconfig: ``chkconfig --add dmcc-backend``
7. Set ownership: ``chown -R edrn parts var``.

You'll need to run the tunnel as root by hand once in order for ssh to
question the authenticity of snail.fhcrc.org's RSA key.  The key fingerprint
should be::

    c4:c3:d0:b1:b7:f6:48:2b:51:79:fa:14:cd:a5:52:d4

Once the key's accepted and you see the FHCRC warning banner, interrupt the
tunnel (CTRL+C).  You can then start everything up normally with::

    service dmcc-backend start


Configuring LDAP
================

OpenLDAP's Standalone LDAP server ``slapd`` should already be configured.  If
not, add the following lines to slapd.conf::

    database shell
    suffix "dc=edrn,dc=jpl,dc=nasa,dc=gov"
    rootdn "cn=Manager,dc=edrn,dc=jpl,dc=nasa,dc=gov" rootpw secret
    add /usr/local/dmcc-backend/bin/edrnDMCCSlapd -c /usr/local/dmcc-backend/etc/ldap.cfg
    bind /usr/local/dmcc-backend/bin/edrnDMCCSlapd -c /usr/local/dmcc-backend/etc/ldap.cfg 
    compare /usr/local/dmcc-backend/bin/edrnDMCCSlapd -c /usr/local/dmcc-backend/etc/ldap.cfg
    delete /usr/local/dmcc-backend/bin/edrnDMCCSlapd -c /usr/local/dmcc-backend/etc/ldap.cfg
    modify /usr/local/dmcc-backend/bin/edrnDMCCSlapd -c /usr/local/dmcc-backend/etc/ldap.cfg
    modrdn /usr/local/dmcc-backend/bin/edrnDMCCSlapd -c /usr/local/dmcc-backend/etc/ldap.cfg
    search /usr/local/dmcc-backend/bin/edrnDMCCSlapd -c /usr/local/dmcc-backend/etc/ldap.cfg
    unbind /usr/local/dmcc-backend/bin/edrnDMCCSlapd -c /usr/local/dmcc-backend/etc/ldap.cfg
    TLSCACertificateFile /usr/local/dmcc-backend/cancer-ldap.pem
    TLSCertificateFile /usr/local/dmcc-backend/cancer-ldap.pem
    TLSCertificateKeyFile /usr/local/dmcc-backend/cancer-ldap.pem

Adjust paths as necessary.


.. References:
.. _DMCC: http://goo.gl/AN6Y
.. _EDRN: http://edrn.nci.nih.gov/
.. _IC: http://cancer.jpl.nasa.gov/
.. _Python: http://python.org/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
