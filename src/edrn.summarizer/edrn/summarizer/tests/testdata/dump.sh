#!/bin/sh
#
# First establish tunnel:
# ssh -L 8443:perdy.fhcrc.org:443 ssc@snail.fhcrc.org
#
# Then run this.  Adjust perdy.fhcrc.org to some other host if needed.

# Grab the WSDL
rm -f wsdl.xml
curl -k -H 'Host: perdy.fhcrc.org' -H 'Content-type: application/soap+xml; charset=utf8' \
    'https://localhost:8443/edrn_ws/ws_newcompass.asmx?WSDL' \
    | sed -e 's=https://perdy.fhcrc.org/edrn_ws=testscheme://localhost=g' > wsdl.xml

# Grab each DMCC Ontology information response
for kind in Body_System Committee_Membership Committees Disease EDRN_Protocol Protocol_Protocol_Relationship Protocol_Registered_Person_Specifics Protocol_Site_Specifics Protocol_or_Study Publication Registered_Person Site tlkpProtocolSiteRoles tlkpReportingStages; do
    rm -f "$kind.xml" /tmp/command.xml
    cat >/tmp/command.xml <<EOF
<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
  <soap12:Body>
    <$kind xmlns="http://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx">
      <verificationNum>0</verificationNum>
    </$kind>
  </soap12:Body>
</soap12:Envelope>
EOF
    curl -k -H 'Host: perdy.fhcrc.org' -H 'Content-type: application/soap+xml; charset=utf8' \
    --data-binary @/tmp/command.xml https://localhost:8443/edrn_ws/ws_newcompass.asmx > "$kind.xml"
done
