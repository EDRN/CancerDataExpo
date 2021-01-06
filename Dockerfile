# Dockerfile
# ==========
#
# Defines the image for the CancerDataExpo

FROM plone:5.2.2-alpine

ENV numpy=1.19.3

COPY site.cfg /plone/instance/
COPY src/ /plone/instance/src/
COPY etc/ /plone/instance/etc/

RUN : &&\
    build_deps="gcc musl-dev" &&\
    apk update --quiet &&\
    apk add --quiet --virtual /build $build_deps &&\
    pip --quiet install numpy==${numpy} &&\
    buildout -c site.cfg &&\
    find /plone -not -user plone -exec chown plone:plone {} \+ &&\
    apk del --quiet /build &&\
    rm -rf /var/cache/apk/* &&\
    :
