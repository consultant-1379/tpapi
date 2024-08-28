'''User Acceptance test for UseCase 2

As a TP developer I want to be able to modify an existing TP based on changes in an XML file; the XML file shall adhere to the IWD.

It is not required to be able to modify/create every aspect of a TP; it is expected that the following will be possible by manipulating/updating/creating repdb content:

    Update existing TP tables with new columns
    Create new TP tables and add columns to them

It is not required to be able to do this to a .tpi file; all modify/create operations will execute against repdb on a development ENIQ server.

It shall be possible to:
1. read the existing TP from an ENIQ server
2. read the updated TP from XML
3. compare the two versions of the TP
4. update the TP in repdb (for the attributes outlined above)

Acceptanace criteria:

    Modified TP will reflect the content of the XML for the attributes outlined above
    Javadoc for the various API methods developed
    Methods include exception handling and log issues/errors to a common log file

Created on 24 Aug 2012
'''
import TPAPI
import time            
startTime = time.time()
debug = True

''' 
1) identify highest version of testcase TP installed on server. 
2) get details from server
3) write details to XML.
4) read XML into elementTree structure
5) increment version ID 
6) amend existing details in elementTree
7) add new details to elementTree
8) write updated details to XML
9) read XML
10) update testcase TP on server
11) read updated testcase TP from server 
12) compare with original testcase TP from server
13) fail if any unintended changes identified
14) fail if any intended changes not implemented    
''' 

#---------------------------
# Main
#---------------------------
print 'Starting Use case 2 tests' 
# run test one
server = "atrcx699.athtem.eei.ericsson.se" # change to a local server

print '1) identify highest version of testcase TP installed on server.'
tp1 = TPAPI.TechPack('DC_S_TEST')
#tp1 = TPAPI.TechPack('DC_E_CPG')
tpvlist = tp1.getInstalledVersions(server)
if debug:
    print tpvlist
    
if tpvlist is None or len(tpvlist) == 0:
    print 'testcaseTP is not installed on server', server
    raise ValueError('testcaseTP is not installed on server')
tpName = sorted(tpvlist)[-1]
if debug:
    print 'chosen tpv is',tpName

print '2) get details from server'
tpv = TPAPI.TechPackVersion(tpName)
tpv.getPropertiesFromServer(server)    

print '3) write details to XML.'
#This line of code turns abcxyz:((nnn)) into abcxyz_nnn.xml 
filename = tpName.split(':')[0]+'_'+tpName.split(':')[1][2:-2]+'.xml' 
if debug:
    print 'using filename', filename
TPAPI.writeXMLFile(tpv.toXML(), filename)

print '4) read XML into elementTree structure'
from xml.etree import ElementTree

xmlObject = ElementTree.parse(filename)
root = xmlObject.getroot()

print '5) increment version ID'
base = tpName.split(':')[0]
new_vid = str(int(tpName.split(':')[1][2:-2]) + 1) 
new_tpName = base +':(('+new_vid+'))'
new_filename = base+'_'+new_vid+'.xml'
if debug:
    print 'new versionID',new_tpName
    print 'new fileName',new_filename

print '6) amend existing details in elementTree'
for elem in root:
    if elem.tag == 'Versioning': 
        elem.set('name', new_tpName)
        for elem2 in elem:
            if elem2.tag=='VersionInfo':
                for sub in elem2:
                    if sub.tag=='Property' and sub.attrib['key'] == 'VERSIONID':
                        sub.set('val', new_tpName)
                        break
                break
        break                
else:
    if debug:        
        print'Unable to interpret XML file!'
    raise ValueError('Unrecognised XML format')

print '8) write updated details to XML'
tree = ElementTree.ElementTree(root)
tree.write(new_filename)
   
print '9) read XML'
tpv2 = TPAPI.TechPackVersion(new_tpName)
tpv2.getPropertiesFromXML(filename=new_filename)

delta = tpv.difference(tpv2)
if debug:
    print '.oOo'*10
    print delta.toString
    print '.oOo'*10

print ' not done yet ...'
print '''
7) add new details to elementTree
10) update testcase TP on server
11) read updated testcase TP from server 
12) compare with original testcase TP from server
13) fail if any unintended changes identified
14) fail if any intended changes not implemented    '
'''
endTime = time.time()
print "done in ", endTime - startTime