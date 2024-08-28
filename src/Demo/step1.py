'''
Created on 10 Apr 2012

Get the details of a teckpack from a server and store it in an xml file

@author: esmipau + esalste
'''

import TPAPI

server="atrcx888zone3.athtem.eei.ericsson.se"
VersionID='DC_E_BSS:((49))'
Filename='DC_E_BSS_49.xml'


tpv = TPAPI.TechPackVersion(VersionID)
tpv.getPropertiesFromServer(server)
TPAPI.writeXMLFile(tpv.toXML(), Filename)

print 'The details of the techpack',VersionID,'have been stored in the file:',Filename


