***************
 The Test Data
***************

This directory contains fake SOAP responses so we can test the EDRN SUMMARIZER service.
These responses come from the DMCC's SOAP service but have been altered to work
in a test environment.


Generating the Test Data
========================

To generate a fresh copy of the test data, we need to:

1. Grab the WSDL file and transform its SOAP ports.
2. Grab each SOAP response for the information we want the Summarizer server to
   present.
3. Update the functional tests in edrn/summarizer/README.txt to reflect new data.


Generating the WSDL
-------------------

Run the following command to grab a copy and transform the WSDL for the DMCC's
SOAP service (adjust hostnames as necessary)::

    curl -Lk -v 'https://perdy.fhcrc.org/edrn_ws/ws_newcompass.asmx?WSDL' \
    | sed -e 's=https://perdy.fhcrc.org/edrn_ws=testscheme://localhost=g' \
    > wsdl.xml

As a reminder, the DMCC runs SOAP services on the following URLs:

Development (bleeding edge and changing)
    https://pongo.fhcrc.org/edrn_ws/ws_newcompass.asmx?WSDL
Testing (preparing to go into operations)
    https://perdy.fhcrc.org/edrn_ws/ws_newcompass.asmx?WSDL
Operations (stable and authoritative)
    https://www.compass.fhcrc.org/edrn_ws/ws_newcompass.asmx?WSDL


Generating SOAP Responses
-------------------------

Edit the dump.sh script as needed for the host to use (pong, perdy, etc.) then
run it.  Don't forget to establish an SSH tunnel as stated in the script.

