'''User Acceptance test for UseCase 1

As a TP tester I want to be able to export the content of a TP to an XML; this will allow me to analyse the TP and view/parse the content of a TP.

It is not required to deliver a full tool to do execute this function; rather it shall be possible to:
1. Read from server/.tpi
2. Serialise to XML

Acceptance criteria:

    It shall be possible to do this for a TP installed on a server or from a .tpi file
    XML shall accurately display details of all TP content as defined in IWD
    Javadoc for the various API methods developed
    Methods include exception handling and log issues/errors to a common log file

Created on 22 Aug 2012
'''
'''
Additional tests:
   read serialised tecpack and compare it to original. Fail if changes detected 
'''
import TPAPI
import random
import glob
import time            
import logging

class UC1(object):
    ''' Acceptence tests for Use case 1
    The method prepare() must be called before any tests can be run '''

    def __init__(self):
        self.logger = logging.getLogger('TPAPI.Acceptance.UC1')
        self.debug = True
        self.server = None
        self.tpName = None
        self.prepared = False # tests wont run until this is true

    def setServer(self,serverName):
        ''' set the name of the server to use'''
        if serverName is None:
            if self.server is None:
                self.server = "atrcx888zone3.athtem.eei.ericsson.se" # use the default server
        else: 
            self.server = serverName
        if self.debug:print 'server set to ',self.server
        
    def setTPname(self,tpName):
        ''' set the name of the techpack to use'''
        if tpName is None:
            if self.tpName is None:
                #pick a random teckpack from the server
                self.tpName = self._getRandTP()
        else: 
            self.tpName = tpName
        if self.debug: print 'tpName is set to', self.tpName
        
    def setDebug(self,debug):
        ''' enable or disable debug output '''
        self.debug = False
        if debug is True:
            self.debug = True
            
    def prepare(self, server=None, tp=None, debug=None):
        ''' prepare the test to run. 
        Acceptence tests can not be executed until this method completes,
        use named parameters to override default values'''        
        self.setDebug(debug)
        self.setServer(server) 
        self.setTPname(tp)
        self.prepared = True                
                
    def UC1Test1(self):
        ''' read techpack from server
        write it to XML
        read it from XML 
        compare it to what was read from server
        return True if no differences
        ''' 
        tpname = self.tpName
        tpv1 = TPAPI.TechPackVersion(tpname)
        if self.debug:print 'getting properties from server' 
        tpv1.getPropertiesFromServer(self.server)
        
        #This line of code turns abcxyz:((nnn)) into abcxyz_nnn.xml 
        filename = tpname.split(':')[0]+'_'+tpname.split(':')[1][2:-2]+'.xml' 
        # store details to XML file
        if self.debug:print 'Storing details to XML file '+filename
        TPAPI.writeXMLFile(tpv1.toXML(), filename)
        
        # Read data back in from file
        tpv2 = TPAPI.TechPackVersion(tpname)
        if self.debug:print 'reading properties back in from file' 
        tpv2.getPropertiesFromXML(filename=filename)
        
        # compare what we read from the server with what we read from the file
        delta = tpv1.difference(tpv2)
        if delta.getNumChanges() != 0:
            if self.debug: print 'Fail! Differences detected where there should not be any!'
            errfile = tpname.split(':')[0]+'_'+tpname.split(':')[1][2:-2]+'.diff'
            fp = open(errfile,'w')
            fp.writelines(delta.toString())
            fp.close()
            if self.debug: print 'Differences recorded in '+errfile
            return False 
        return True

    def _getRandTP(self):
        ''' get a random teckpack from the current server'''
        # list all techpacks installed on server  
        if self.debug:print ' get list of techpacks installed on server '+server 
        tpvs = TPAPI.getTechPackVersions(self.server)
        
        #exclude non standard TP's
        tplist = []
        for tp in sorted(tpvs):
            # we are only interested in tech packs with names like abcxyz:((nnn))
            if tp.endswith('))'):
                tplist.append(tp)
        if self.debug: 
            print 'list of installed tech packs'
            for x in tplist:
                print x
        
        # pick a random number between 0 and the number of installed tech packs - that is the one we will work with.
        tpnum = random.randrange(0,len(tplist))
        tpname = tplist[tpnum]
             
        #tpname='DC_E_CPG:((14))'
        if self.debug: print ' techpack chosen for test 1 is '+tpname
        return tpname
    
    def UC1Test2(self, tpifile):
        ''' read techpack from tpifile
        read techpack from server
        compare it to what was read from server
        pass if no differences
        ''' 
        tpv1 = TPAPI.TechPackVersion('TPI_VERSION:((0))')
        if self.debug: print 'reading properties from .tpi file', tpifile 
        tpv1.getPropertiesFromTPI(filename=tpifile)
        
        tpname = tpv1.versioning['VERSIONID']
        self.setTPname(tpname)
                
        #This line of code turns abcxyz:((nnn)) into abcxyz_nnn.xml 
        filename = tpname.split(':')[0]+'_'+tpname.split(':')[1][2:-2]+'.xml' 
        # store details to XML file
        if self.debug:
            print 'Storing details to XML file '+filename
        TPAPI.writeXMLFile(tpv1.toXML(), filename)
        
        tpv2 = TPAPI.TechPackVersion(tpname)
        try:
            tpv2.getPropertiesFromServer(server)
        except:
            if self.debug: print 'TP '+str(tpname)+' from .tpi file '+str(tpifile)+'could not be read from server '+str(self.server)
            return False
    
        # compare what we read from the server with what we read from the file
        delta = tpv1.difference(tpv2)
        if delta.getNumChanges() != 0:
            print 'Fail! Differences detected where there should not be any!'
            errfile = tpname.split(':')[0]+'_'+tpname.split(':')[1][2:-2]+'.diff'
            fp = open(errfile,'w')
            fp.writelines(delta.toString())
            fp.close()
            print 'Differences recorded in '+errfile
            return False 
        return True
    
    def UC1Test3(self, server, filename):
        ''' submit specified xmlfile to external verification engine to ensure it is valid
        pass if XML is valid
        ''' 
        
        # TODO implement after DTD is implemented
        print 'Test case dependent on DTD implementation.'
        return False

if __name__ == '__main__':
    startTime = time.time()
    tc = UC1()
    #server = "atrcx699.athtem.eei.ericsson.se" # change to a local server
    server = "10.59.131.124"
    # tp='DC_E_CPG:((14))',
    tc.prepare(server, tp='DC_E_TEST:((105))', debug = True)
    
    print 'Starting Use case 1 tests' 
    # run test one

    print 'Running Test 1'
    result = tc.UC1Test1()
    print 'Test 1 result',result 
    
    print 'Running Test 2'
    tpilist = glob.glob("*.tpi")

    if len(tpilist) == 0:
        print ' No .tpi files found, test can not be completed '
    else:
        # do something to pick a tpi file for which the techpack is installed (in tplist)
        tpifile = tpilist[0]
        result = tc.UC1Test2(tpifile)
        print 'Test 2 ', result
    
    endTime = time.time()
    print "done in ", endTime - startTime