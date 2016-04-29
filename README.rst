**************
 DMCC Backend
**************

This is the backend information management and connection protocol system that
maintains data gathered from the Data Management & Coordinating Center
(DMCC_).  The DMCC provides web services and database access for information
vital to the Early Detection Research Network (EDRN_).  The Informatics Center
(IC_) uses that data to implement informatics services for EDRN.

These services include:

* EDRN knowledge environment information via RDF

In the future, these services will include:

* TBD.

Previous versions included:

* Directory lookup backend for EDRN members via LDAP—no longer necessary
  thanks to the DMCC Authorization Interceptor running in Apache Directory
  Server.

The remainder of this document tells how to set up this software.


Requirements
============

This software requires Python_ 2.7.  On the host cancer.jpl.nasa.gov, a
compatible Python is available in /usr/local/python/parts/opt/bin/python2.7.
Or you can use a compatible virtualenv_.

If a reverse proxy accelerator (such as the Varnish Cache) runs in front of
the DMCC Backend, please configure it to not cache the RDF data produced by
the backend.


Deployment
==========

To deploy this software, do the following:

1. Extract it to a convenient location, say /usr/local/cancerdataexpo.
2. Change the current working directory to that location.
3. Edit the ops.cfg file and change the usernames + passwords!
4. Bootstrap it: ``python2.7 bootstrap.py -c``
5. Build it: ``bin/buildout -c ops.cfg``
6. Create the app server instance:
   ``bin/buildout -c ops.cfg install dmcc-appserver``
7. Install the init script:
   ``install -o root -g root -m 755 bin/cancerdataexpo /etc/init.d``
8. Install the cron job:
   ``install -o root -g root -m 755 bin/update-rdf /etc/cron.daily/edrn-update-rdf``
   ``install -o root -g root -m 755 bin/update-summary /etc/cron.daily/edrn-update-summary``
9. Add to chkconfig: ``chkconfig --add cancerdataexpo``
10. Set ownership: ``chown -R edrn parts var``.

You can then start it all up with::

    service cancerdataexpo start


.. References:
.. _DMCC: http://goo.gl/AN6Y
.. _EDRN: http://edrn.nci.nih.gov/
.. _IC: http://cancer.jpl.nasa.gov/
.. _Python: http://python.org/
.. _virtualenv: http://pypi.python.org/pypi/virtualenv
