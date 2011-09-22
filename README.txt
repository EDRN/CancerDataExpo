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

In the future, these services will include:

* EDRN knowledge environment information via RDF

The remainder of this document tells how to set up this software.


Requirements
============

This software requires Python_ 2.6.  On the host cancer.jpl.nasa.gov, a
compatible Python is available in /usr/local/python/parts/opt/bin/python2.6.
Or you can use a compatible virtualenv_.


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

You can then start it up: ``service dmcc-backend start``.


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
