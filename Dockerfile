# Dockerfile
# ==========
#
# Defines the image for the CancerDataExpo
#
# Going beyond 5.2.9 seems to break things
#
# We should dump Plone/Zope and switch to Django

FROM plone:5.2.9

ENV numpy=1.23.4

COPY site.cfg /plone/instance/
COPY src/ /plone/instance/src/
COPY etc/ /plone/instance/etc/

RUN : &&\
    pip --quiet install numpy==${numpy} &&\
    buildout -c site.cfg &&\
    find /plone -not -user plone -exec chown plone:plone {} \+ &&\
    :

