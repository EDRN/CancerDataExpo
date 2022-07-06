# 🎪 The Cancer Data Exposition


This is the backend information management and connection protocol system that maintains data gathered from the [Data Management & Coordinating Center](https://tinyurl.com/ybkp7c7z) and other sources.  The DMCC provides web services and database access for information vital to the [Early Detection Research Network](https://edrn.nci.nih.gov/).  The Informatics Center uses that data to implement informatics services for EDRN.

These services include:

- ESIS information via RDF
- Biomuta information via RDF
- Summary information via JSON

In the future, these services could include:

- ERNE speciemn data

Previous versions included:

- Directory lookup backend for EDRN members via LDAP—no longer necessary
  thanks to the DMCC Authorization Interceptor running in Apache Directory
  Server

The remainder of this document tells how to set up and debug this software.


## 🐛 Manually Making SOAP Requests

Okay, so you need to look at the awful, horribly-formatted raw data from the DMCC's ignominious SOAP service. Here's how you do that:

First, visit https://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx and pick one of the operations to exercise, say, "Disease". Click it and look under the SOAP 1.1 section. The first box is the request, so make a file with the request body text, i.e., with:

```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <Disease xmlns="http://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx">
            <verificationNum>0</verificationNum>
        </Disease>
    </soap:Body>
</soap:Envelope>
```

Note that you replace "string" with "0". Don't ask why—it's dumb 🙄. Save that as `/tmp/req.xml`. Next note that there's a `SOAPAction` header, so we need to duplicate that. So, run this command:

```console
curl --http1.1 --verbose --request POST \
    --header 'SOAPAction: "http://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx/Disease"' \
    --header 'Content-type: text/xml; charset=utf-8' \
    --data @/tmp/req.xml \
    'https://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx?WSDL' > /tmp/result.xml
```

The answer will then be in the result element of the response element of the envelope element of the XML document in `/tmp/result.xml`.


## 🔧 Developing

**👉 Note:** Plone 5.2.2 (used here) is not compatible with any Python newer than 3.8. Stick with 3.8.

Do the following:
```console
python3.8 -m venv venv
venv/bin/pip install --upgrade pip build wheel zc.buildout setuptools==42.0.2 numpy==1.19.3
venv/bin/buildout -c dev.cfg
```

You can then run: `bin/zope-debug fg`.


## 🚀 Deploying the Cancer Data Expo

Here are the environment variables you'll need to set (substituting values between development and production):

-   `EDRN_CANCERDATAEXPO_DATA` — set to a path to contain blobstorage, filestorage, and logs.
-   `EDRN_CANCERDATAEXPO_PORT` — set to a free port number
-   `EDRN_CANCERDATAEXPO_VERSION` — set to a version number or `latest`
-   `EDRN_IMAGE_OWNER` — set to `nutjob4life` or leave it blank to use your local Docker images


### 🧱 Building the Image

Just run:

    docker image build --tag cancerdataexpo .

To publish it:

    docker login
    docker image tag cancerdataexpo:latest nutjob4life/cancerdataexpo:latest
    docker image push nutjob4life/cancerdataexpo:latest


### 🏃‍♀️ Running the CancerDataExpo

To run the CancerDataExpo for the **first time**, create empty directories to hold the blobstorage, filestorage, and logs, then start the composition:

    mkdir -p $EDRN_CANCERDATAEXPO_DATA/blobstorage
    mkdir -p $EDRN_CANCERDATAEXPO_DATA/filestorage
    mkdir -p $EDRN_CANCERDATAEXPO_DATA/log
    env \
        EDRN_CANCERDATAEXPO_DATA=/usr/local/labcas/cancerdataexpo/docker-data \
        EDRN_CANCERDATAEXPO_VERSION=latest \
        EDRN_CANCERDATAEXPO_PORT=2131 \
        docker-compose \
            --project-name cancerdataexpo \
            up --detach

The `docker-compose.yaml` assumes that `EDRN_CANCERDATAEXPO_DATA` is `/usr/local/labcas/cancerdataexpo/docker-data` which is appropriate for `edrn-docker.jpl.nasa.gov` where this normally runs, and that `EDRN_CANCERDATAEXPO_PORT` is 2131, and that `EDRN_CANCERDATAEXPO_VERSION` is `latest`, so you can simply say:

    docker-compose --project-name cancerdataexpo up --detach

You can check the logs with:

    docker-compose --project-name cancerdataexpo logs --follow

**📝 Note:** With no existing database, the initiall startup might fail (see the logs, message "Resource Busy"). If this happens, stop it and start it again.

Once this is up and running, head to http://localhost:${EDRN_CANCERDATAEXPO_PORT}/manage_main and log in (with username `admin` and password `admin`) and change the default password in the `acl_users` object. Next, create an instance of the CancerDataExpo by visiting http://localhost:${EDRN_CANCERDATAEXPO_PORT}/@@plone-addsite?site_id=Plone&advanced=1 and entering the following:

-   Path identifier: `cancerdataexpo`
-   Title: Cancer Data Expo
-   Default timezone: UTC
-   Example content: OFF
-   Add-ons:
    -   Barceloneta Theme
    -   HTTP caching support
    -   "Cancer Data Expo" Policy

And click "Create Plone Site". Then, from the "admin" button in the corner, go to Site Setup → LDAP/AD Support and enter:

-   Manager User: `uid=admin,ou=system`
-   Manager Password: (enter the correct password)
-   Memcached server to use: `memory-cache:11211`

Then click "Save". Lastly, head to the RDF Generators and give the LabCAS generator a username and password that has "Super User" permissions to query LabCAS. And fianlly ask your friendly sysadmins to reverse-proxy.

Need to bring it all down?

    docker-compose --project-name cancerdataexpo down


### 🎽 Subsequent Runs

Start it up again?

    docker-compose --project-name cancerdataexpo up --detach


#### 🐛 Advanced Debugging

Need to access the Zope debug console from a running Docker Composition? This section's for you.

Get to the Zope debug prompt with the `cancerdataexpo` as the active site:

    docker container run --volume ${EDRN_CANCERDATAEXPO_DATA}/blobstorage:/data/blobstorage --tty --rm --interactive --network cancerdataexpo_frontsidebus --env ZEO_ADDRESS=db:8080 --env ZEO_SHARED_BLOB_DIR=on cancerdataexpo:latest debug -O cancerdataexpo

Add a Manager user (not through the web, like above):

    docker container run --volume ${EDRN_CANCERDATAEXPO_DATA}/blobstorage:/data/blobstorage --tty --rm --interactive --network cancerdataexpo_frontsidebus --env ZEO_ADDRESS=db:8080 --env ZEO_SHARED_BLOB_DIR=on cancerdataexpo:latest adduser USERNAME PASSWORD


Get a shell:

    docker container run --volume ${EDRN_CANCERDATAEXPO_DATA}/blobstorage:/data/blobstorage --tty --rm --interactive --network cancerdataexpo_frontsidebus --entrypoint /bin/bash cancerdataexpo:latest
