'''
Created on 10 Apr 2012

Implement changes on server

@author: esmipau + esalste
'''

import TPAPI

# load the details from the first XML file
OldVersionID='DC_E_BSS:((49))'
OldFilename='DC_E_BSS_49.xml'

tpv1 = TPAPI.TechPackVersion(OldVersionID) 
tpv1.getPropertiesFromXML(filename=OldFilename)

# load the details from the second XML file
NewVersionID='DC_E_BSS:((50))'
NewFilename='DC_E_BSS_50.xml'

tpv2 = TPAPI.TechPackVersion(NewVersionID)
tpv2.getPropertiesFromXML(filename=NewFilename)

# compare the two xml tech packs.
delta = tpv1.difference(tpv2)

# Update the server with the changes
server="atrcx888zone3.athtem.eei.ericsson.se"
tpv1.update(delta, server)



 

