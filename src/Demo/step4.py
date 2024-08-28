'''
Created on 10 Apr 2012

Verify the differences on the server

@author: esmipau + esalste
'''

import TPAPI

server="atrcx888zone3.athtem.eei.ericsson.se"
# load the details from server for the original TP
VersionID='DC_E_BSS:((49))'

tpv1 = TPAPI.TechPackVersion(VersionID) 
tpv1.getPropertiesFromServer(server)

# load the details from server for the updated TP
NewVersionID='DC_E_BSS:((50))'


tpv2 = TPAPI.TechPackVersion(NewVersionID)
tpv2.getPropertiesFromServer(server)

# compare the two tech packs.
delta = tpv1.difference(tpv2) 
print "Techpack diff:" + tpv1.tpName + ":" + tpv1.versionID + " vs "  + tpv2.tpName + ":" + tpv2.versionID, "on server", server
print "*************************************************"
print delta.toXML()
print delta.deltaTPVtoXML()

