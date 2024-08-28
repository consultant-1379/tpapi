#!/usr/bin/python
# -*- coding: latin-1 -*-

'''
Created on 13 Nov 2012

@author: ebrifol
'''

import TPAPI
import sys
import os
import logging
import traceback
from optparse import OptionParser


logging.basicConfig(filename='DifTool.log',level=logging.DEBUG)
outputPath = os.getcwd()

def main():
    logging.info('DifTool tool started!')

    if len(sys.argv) <= 1 or options.help:
        printUsage()
    else:
        processParams()


def processParams():
    sourcetechpack = None
    targettechpack = None
    
    print 'Loading source and target techpacks'
    logging.info('Loading source and target techpacks')
    '''
        Loading from the server
    '''
    if options.sourceserver != None or options.sourcetp != None:
        sourcetechpack = loadfromServer(options.sourceserver, options.sourcetp)
    if options.targetserver != None or options.targettp != None:
        targettechpack = loadfromServer(options.targetserver, options.targettp)
    
    '''
        Loading from XML input files
    '''
    if options.sourcexml != None:
        sourcetechpack = loadfromXML(options.sourcexml)
    if options.targetxml != None:
        targettechpack= loadfromXML(options.targetxml)
   
   
    '''
        Loading from tpi input files
    '''
    if options.sourcetpi != None:
        sourcetechpack = loadfromtpi(options.sourcetpi)
    if options.targettpi != None:
        targettechpack= loadfromtpi(options.targettpi)
    
    '''
        Optional writing the loaded techpacks to XMl files
    '''  
    if options.xmloutput:
        print 'Writing loaded techpacks to XML'
        logging.info('Writing loaded techpacks to XML')
        if sourcetechpack != None:
            TPAPI.writeXMLFile(sourcetechpack.toXML(), outputPath+'\\'+sourcetechpack.versionID+'.xml')
            print 'Source techpack was writen to '+outputPath+'\\'+sourcetechpack.versionID+'.xml'
            logging.debug('Source techpack was writen to '+outputPath+'\\'+sourcetechpack.versionID+'.xml')
        if targettechpack != None:
            TPAPI.writeXMLFile(targettechpack.toXML(), outputPath+'\\'+targettechpack.versionID+'.xml')
            print 'Target techpack was writen to '+outputPath+'\\'+targettechpack.versionID+'.xml'
            logging.debug('Target techpack was writen to '+outputPath+'\\'+targettechpack.versionID+'.xml')
    
    
    '''
        Only preform difference if two valid techpacks have been loaded
    '''
    if sourcetechpack != None and targettechpack != None:
        '''
            Preforming the difference between two techpacks
        ''' 
        logging.info('Preforming difference between '+sourcetechpack.versionID+' and '+targettechpack.versionID)
        print 'Preforming difference between '+sourcetechpack.versionID+' and '+targettechpack.versionID
        techpackdelta = sourcetechpack.difference(targettechpack)
        
        
        '''
            Optional output of difference results to a file otherwise they are printed to the std out
        '''
        if options.diffoutput:
            f = open(outputPath+'\\deltaOuput.txt','w')
            f.write(techpackdelta.toString())
            f.close()
            print 'Difference result was writen to '+outputPath+'\\deltaOuput.txt'
            logging.info('Difference result was writen to '+outputPath+'\\deltaOuput.txt')
        else:
            print '----- Difference Results -----'
            print techpackdelta.toString()
            logging.info('Difference result was writen to std out')
    
   
     
def loadfromServer(server, techpackID):
    techpack = None
    if server != None and techpackID != None:
        techpack = TPAPI.TechPackVersion(techpackID)
        print 'collecting techpack'
        techpack.getPropertiesFromServer(server)
        print 'properties collected from server'
        print techpackID + ' was loaded from ' + server
        logging.debug(techpackID + ' was loaded from ' + server)    
    elif server != None and techpackID == None:
        isntalledtps = TPAPI.getTechPackVersions(server)
        print 'No techpack version ID was given. The following techpacks are installed on '+server+':'
        for tpVersions in isntalledtps:
            print tpVersions
    else:
        print 'Server name and techpack version ID are required to retrieve a techpack from a server'

    return techpack

def loadfromXML(path):
    techpack = None
    try:
        techpack = TPAPI.TechPackVersion()
        techpack.getPropertiesFromXML(filename=path)
        print techpack.versionID + ' was loaded from XML input file ' + path
        logging.debug(techpack.versionID + ' was loaded from XML input file ' + path)
    except:
        print 'Input XML file '+ path +' was not valid'
        
    return techpack

def loadfromtpi(path):
    techpack = None
    try:
        techpack = TPAPI.TechPackVersion()
        techpack.getPropertiesFromTPI(filename=path)
        print techpack.versionID + ' was loaded from tpi input file ' + path
        logging.debug(techpack.versionID + ' was loaded from tpi input file ' + path)
    except:
        traceback.print_exc(file=sys.stdout)
        print 'Input tpi file '+ path +' was not valid'
    return techpack   
    

def printUsage():
    print '''---------------------------------------------------------------------------------------------------  
    Name: DifTool.py
    
    Description:
     Tool to demo loading from a server, tpi or xml and preforming the difference between two techpacks.
     Can export techpacks to XML file and write differences to output file
    
    Command:
     python DifTool.py [-ss <source server> [-–stp <source techpack version>] | -sx <source XML> | -sf <sourceTPI file>] 
         [ -ts <target server> [-–ttp <target techpack version>] | -tx <target XML> | -tf <target TPI file> ] 
         -xo -do

    
    Command options:
     --ss    --sourceserver     Server name where source techpack is loaded from 
                                i.e. atrcx888zone3.athtem.eei.ericsson.se

     --stp   --sourcetp         Version ID of source techpack. Must exist on the sourceserver
                                i.e. DC_S_TEST:((20)) 
    
     --sx    --sourcexml        Absolute path to source xml file
     --sf    --sourcefile       Absolute path to source tpi file
    
     --ts    --targetserver     Server name where test techpack is loaded from
                                i.e. atrcx888zone3.athtem.eei.ericsson.se
    
     --ttp   --targettp         Version ID of target techpack. Must exist on the targetserver
                                i.e. DC_S_TEST:((20))
    
     --tx    --targetxml        Absolute path to target xml file
     --tf    --targetfile       Absolute path to target tpi file
    
     --xo    --xmloutput        Write XML for loaded techpacks to output file
     --do    --diffoutput       Write difference results to output file
---------------------------------------------------------------------------------------------------'''
    sys.exit(' ')
  
  
'''
    Parse in the command line arguments
'''   
try:
    parser = OptionParser(conflict_handler="resolve")
    parser.add_option("--ss", "--sourceserver", dest="sourceserver",
                      help="Source server name", metavar="SSERVER")
        
    parser.add_option("--stp", "--sourcetp", dest="sourcetp",
                      help="Version ID of source techpack", metavar="STPID")
    
    parser.add_option("--sx", "--sourcexml", dest="sourcexml",
                      help="File path for source XML file", metavar="SXML")
    
    parser.add_option("--sf", "--sourcefile", dest="sourcetpi",
                      help="File path for source tpi file", metavar="STPI")
    
    parser.add_option("--ts", "--targetserver", dest="targetserver",
                      help="Target server name", metavar="TSERVER")
    
    parser.add_option("--ttp", "--targettechpack", dest="targettp",
                      help="Version ID of target techpack", metavar="TTPID")
    
    parser.add_option("--tx", "--targetxml", dest="targetxml",
                     help="File path for target XML file", metavar="TP2")
    
    parser.add_option("--tf", "--targetfile", dest="targettpi",
                      help="Output Filename", metavar="FILENAME")
    
    parser.add_option("--xo", "--xmlouput", action="store_true", dest="xmloutput", 
                      default=False, help="Print input techpacks to XML files")
    
    parser.add_option("--do", "--diffoutput", action="store_true", dest="diffoutput",
                     default=False, help="Print difference results to txt file")
    
    parser.add_option("-h", "--help", action="store_true", dest="help",
                     default=False, help="Prints the usage of the script")
    
    (options,args) = parser.parse_args()
except:
    traceback.print_exc(file=sys.stdout)
    printUsage()   
    
#-------------------------------
if __name__ == "__main__":
    main()
