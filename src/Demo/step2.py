'''
Created on 10 Apr 2012

Identify the changes we are planning to make

@author: esmipau + esalste
'''

import TPAPI
 
# load the details from the first XML file
VersionID='DC_E_BSS:((49))'
Filename='DC_E_BSS_49.xml'
tpv1 = TPAPI.TechPackVersion(VersionID) 
tpv1.getPropertiesFromXML(filename=Filename)

# load the details from the second XML file
NewVersionID='DC_E_BSS:((50))'
NewFilename='DC_E_BSS_50.xml'

tpv2 = TPAPI.TechPackVersion(NewVersionID)
tpv2.getPropertiesFromXML(filename=NewFilename)

# compare the two tech packs.
delta = tpv1.difference(tpv2) 
print "Techpack diff:" + tpv1.tpName + ":" + tpv1.versionID + " vs "  + tpv2.tpName + ":" + tpv2.versionID
print "*************************************************"

print delta.toXML()
print delta.deltaTPV.toXML()


