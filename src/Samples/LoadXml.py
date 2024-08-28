'''
Created on 20 Nov 2012

@author: ebrifol
'''

import TPAPI
import logging
import os
import re
import time

logging.basicConfig(filename='LoadXml.log',level=logging.DEBUG)
TPAPI.logger

def main():
    logging.getLogger('LoadXml')
    
    initstart = time.time()
    server = "atrcx888zone3.athtem.eei.ericsson.se"
    versionID = 'DC_E_CUDB:((21))'
    path = os.getcwd()
    path = re.sub('\\XML$', '\Inputs', path )
    tpipath = path+'\\Unencrypted_DC_E_CUDB_R8B_b10021.tpi'
    
    logging.info('XMLTool tool started!')
    print 'XMLTool tool started!'
    
    logging.info('Loading Techpack from server')
    print 'Loading Techpack from server'
    startTime = time.time()
    serverTp = loadTPfromServer(versionID, server)
    endTime = time.time()
    totaltime = endTime - startTime
    logging.info(serverTp.versionID+' loaded from ' + server +' in ' + str(totaltime))
    print serverTp.versionID+' loaded from ' + server +' in ' + str(totaltime)
    
    logging.info('Loading Techpack from tpi file')
    print 'Loading Techpack from tpi file'
    startTime = time.time()
    tpiTp = loadTPfromTPI(tpipath)
    endTime = time.time()
    totaltime = endTime - startTime
    logging.info(tpiTp.versionID+' loaded from ' + tpipath +' in ' + str(totaltime))
    print tpiTp.versionID+' loaded from ' + tpipath +' in ' + str(totaltime)
    
    logging.info('Writing to XML')
    print 'Writing to XML'
    startTime = time.time()
    
    TPAPI.writeXMLFile(serverTp.toXML(), path+"\\Server.xml")
    logging.info('Server.xml was written to '+path)
    print 'Server.xml was written to '+path
    
    TPAPI.writeXMLFile(tpiTp.toXML(), path+"\\Tpi.xml")
    logging.info('Tpi.xml was written to '+path)
    print'Tpi.xml was written to '+path  
    
    
    delta = serverTp.difference(tpiTp)
    f = open(path+'\\deltaOuput.txt','w')
    f.write(delta.toString())
    f.close()
    

def loadTPfromServer(versionID, server):
    tpv = TPAPI.TechPackVersion(versionID)
    tpv.getPropertiesFromServer(server)
    return tpv

def loadTPfromTPI(path):
    tpv = TPAPI.TechPackVersion()
    tpv.getPropertiesFromTPI(filename=path)
    return tpv

def loadTPfromXML(path):
    tpv = TPAPI.TechPackVersion()
    tpv.getPropertiesFromXML(filename=path)
    return tpv

#-------------------------------
if __name__ == "__main__":
    main()
