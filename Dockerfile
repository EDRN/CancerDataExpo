# Dockerfile
# ==========
#
# Defines the image for the CancerDataExpo

FROM plone:5.2.14

ENV numpy=1.23.4

COPY site.cfg /plone/instance/
COPY src/ /plone/instance/src/
COPY etc/ /plone/instance/etc/

RUN : &&\
    pip --quiet install numpy==${numpy} &&\
    buildout -c site.cfg &&\
    find /plone -not -user plone -exec chown plone:plone {} \+ &&\
    :

