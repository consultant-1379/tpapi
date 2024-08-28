'''
Created on 24 Jan 2013

@author: ebrifol
'''

import TPAPI
import inspect
import sys
import traceback
import os
import shutil
from optparse import OptionParser

cwd = os.getcwd()

excessNames = ['itertools','Runtime','zxJDBC','tpiDict_old','Universe','UniverseCondition','UniverseJoin','UniverseObject', 'UniverseTable', 'TPAPILogger']
pageStart = '''<HTML><HEAD><TITLE>'''
Headerp1 = '''</TITLE>
<BODY BGCOLOR="white" onload="windowTitle();">
<HR>
<TABLE BORDER="0" WIDTH="100%" CELLPADDING="1" CELLSPACING="0" SUMMARY="">
<TR>
<TD ALIGN="center" VALIGN="top" ROWSPAN=3><H2><EM>
<b>TechPack API<br>'''
Headerp2 = '''</b></EM></H2>
</TD>
</TR>
</TABLE>
<HR>
'''

def main():

    if len(sys.argv) <= 1 or options.help:
        printUsage()
    else:
        describe_main(TPAPI)
    print "Script complete!"


def describe_func(obj):
    arguments = '('
    defaultargs = ''
    try:
        arginfo = inspect.getargspec(obj)

        args = arginfo[0]
        if args:
            if args[0] == 'self':
                args.pop(0)

            for arg in args:
                if arguments != '(':
                    arguments = arguments + ', '
                arguments = arguments + arg
            arguments = arguments + ')'
        
        if arginfo[3]:
            dl = len(arginfo[3])
            al = len(args)
            defargs = args[al-dl:al]
            defaultargs = zip(defargs, arginfo[3])

    except TypeError:
        pass
    
    funcContents = [] 
    funcContents.append('''<TR BGCOLOR="white" CLASS="TableRowColor">
    <TD ALIGN="left" VALIGN="top" WIDTH="1%"><B>''')
    funcContents.append(obj.__name__+arguments)
    funcContents.append('''</B></TD><TD><B>Description: </B><DL><DD>''') 
    if obj.__doc__ is not None:
        Info = obj.__doc__
        Info = Info.replace("Instance Variables:\n", "</DL><B>Instance Variables:</B><DL><DD>")
        Info = Info.replace("Exceptions:\n", "</DL><B>Exceptions:</B><DL><DD>")
        Info = Info.replace("SQL Statement:\n", "</DL><B>SQL Statement:</B><DL><DD>")
        Info = Info.replace("Return Value:\n", "</DL><B>Return Value:</B><DL><DD>")
        Info = Info.replace("\n", "<BR>")
        funcContents.append(Info)
    
    if len(defaultargs) > 0:
        funcContents.append("</DL><B>Argument Default Values:</B><DL><DD>")
        for tup in defaultargs:
            argName = ''
            argValue = ''
            if tup[0] is not None:
                argName = tup[0]
            else:
                argName = 'None'
                
            if tup[1] is not None:
                argValue = str(tup[1])
            else:
                argValue = 'None'
                
            funcContents.append("<DL><B>Argument Name: </B>"+ argName + " <B>Default value: </B>"+argValue+"</DL>")
        funcContents.append("</DL>")
    funcContents.append('''</TD></TR>''')
    
    return obj.__name__, funcContents


def describe_class(obj):
    classContents = []
    classContents.append("<H2><FONT SIZE=\"-1\">" + obj.__module__ + "</FONT>")
    classContents.append("<BR>Class " + obj.__name__ + "</H2><HR>")
    classContents.append("<P><B>Description:</B><DT>")
    if obj.__doc__ is not None:
        classContents.append(obj.__doc__)
    classContents.append("<HR>")

    constructorContents = []
    constructorContents.append('''<A NAME="method_summary"></A>
    <TABLE BORDER="1" WIDTH="100%" CELLPADDING="3" CELLSPACING="0" SUMMARY="">
    <TR BGCOLOR="#CCCCFF" CLASS="TableHeadingColor">
    <TH ALIGN="left" COLSPAN="2"><FONT SIZE="+2">
    <B>Constructor Summary</B></FONT></TH>
    </TR>''')
    
    hiddenMethods = {}
    publicMethods = {}
    methodContents = []
    methodContents.append('''<A NAME="method_summary"></A>
    <TABLE BORDER="1" WIDTH="100%" CELLPADDING="3" CELLSPACING="0" SUMMARY="">
    <TR BGCOLOR="#CCCCFF" CLASS="TableHeadingColor">
    <TH ALIGN="left" COLSPAN="2"><FONT SIZE="+2">
    <B>Method Summary</B></FONT></TH>
    </TR>''')
    
    for name in obj.__dict__:
        item = getattr(obj, name)
        if inspect.ismethod(item):
            if item.__name__ == '__init__':
                key, value = describe_func(item)
                for line in value:
                    constructorContents.extend(line)
            else:
                key, value = describe_func(item)
                if key.startswith('_'):
                    hiddenMethods[key] = value
                else:
                    publicMethods[key] = value
                #methodContents.extend(describe_func(item))
    
    
    for key in sorted(publicMethods.iterkeys()):
        methodInfo = publicMethods[key]
        for line in methodInfo:
            methodContents.append(line)
            
    if options.designer: 
        for key in sorted(hiddenMethods.iterkeys()):
            methodInfo = hiddenMethods[key]
            for line in methodInfo:
                methodContents.append(line)
           
    constructorContents.append('</TABLE>')       
    methodContents.append('</TABLE>')
    
    if len(constructorContents) > 2:
        classContents.extend(constructorContents)
        classContents.append("<HR>")
    classContents.extend(methodContents)
    
    return classContents

def createUtilsPage():
    utils = []
    utils.append(pageStart)
    utils.append("Utilities")
    utils.append(Headerp1)
    utils.append(options.version)
    utils.append(Headerp2)
    utils.append("<H2><FONT SIZE=\"-1\">TPAPI.TPAPI_Util</FONT>")
    utils.append("<BR>Utilities </H2><HR>")
    utils.append("<P><B>Description:</B><DT>")
    utils.append("These are a collection of useful methods")
    utils.append("<HR>")
    utils.append('''<A NAME="method_summary"></A>
    <TABLE BORDER="1" WIDTH="100%" CELLPADDING="3" CELLSPACING="0" SUMMARY="">
    <TR BGCOLOR="#CCCCFF" CLASS="TableHeadingColor">
    <TH ALIGN="left" COLSPAN="2"><FONT SIZE="+2">
    <B>Method Summary</B></FONT></TH>
    </TR>''')

    return utils

def createIndexPage(createdPages):
    content = []
    content.append(pageStart)
    content.append("TP API Index")
    content.append(Headerp1)
    content.append(options.version)
    content.append(Headerp2)
    content.append('''<TABLE BORDER="1" WIDTH="80%" CELLPADDING="3" CELLSPACING="0" ALIGN="center">
    <TR BGCOLOR="#CCCCFF" CLASS="TableHeadingColor">
    <TH ALIGN="left"><FONT SIZE="+2">
    <B>Name</B></FONT></TH>
    <TH ALIGN="left"><FONT SIZE="+2">
    <B>Description</B></FONT></TH>
    </TR>
    ''')
    
    for key in sorted(createdPages.iterkeys()):
        description = ''
        if createdPages[key] is not None:
            description = createdPages[key]
            
        content.append('''<TR BGCOLOR="white" CLASS="TableRowColor"><TD ALIGN="left" VALIGN="top" WIDTH="1%"><B>''')
        content.append('''<a href="'''+key+'''.html">''')
        content.append(key)
        content.append('''</a></B></TD><TD>''')
        content.append(description + '</TD></TR>')
    
    content.append('''</TABLE><HR></BODY></HTML>''')
    
    file = open(cwd +'\\Index.html', 'w')
    for line in content:
        file.write(line)
    file.close()
        

def createOutputDir():
    global cwd
    if options.designer: 
        cwd = cwd + '\\output\\' + options.version + '_TPAPI-Designer'
    else:
        cwd = cwd + '\\output\\' + options.version + '_TPAPI-User'
    
    if os.path.exists(cwd):
        shutil.rmtree(cwd)
        os.makedirs( cwd , 0755 );
    else:
        os.makedirs( cwd , 0755 );  

def describe_main(module):
    createOutputDir()
    utils = []
    utils.extend(createUtilsPage())
    hiddenUtils = {}
    publicUtils = {}
    Indexinfo = {}
    createdFiles = {}
    createdFiles ['Utils'] = "These are a collection of useful methods"  
    for name in dir(module):
        obj = getattr(module, name)
        filecontents = []
        filecontents.append('''<a href="index.html">Index</a>''')
        filecontents.append(pageStart)
        
        if inspect.isclass(obj):
            if obj.__name__ not in excessNames:
                filecontents.append(obj.__name__)
                filecontents.append(Headerp1)
                filecontents.append(options.version)
                filecontents.append(Headerp2)
                filename = obj.__name__
                filecontents.extend(describe_class(obj))
                Indexinfo[obj.__name__] = obj.__doc__
        elif (inspect.ismethod(obj) or inspect.isfunction(obj)):
            key, value = describe_func(obj)
            if key.startswith('_'):
                hiddenUtils[key] = value
            else:
                publicUtils[key] = value
        elif inspect.isbuiltin(obj):
            print obj.__name__
            pass
        
        filecontents.append('''<HR></BODY></HTML>''')

        if len(filecontents) > 200 and not os.path.exists(cwd +'\\' +filename+'.html'):
            createdFiles[filename] = Indexinfo[filename]
            file = open(cwd +'\\' +filename+'.html', 'w')
            for line in filecontents:
                file.write(line)
            file.close()
    
    
    for key in sorted(publicUtils.iterkeys()):
        methodInfo = publicUtils[key]
        for line in methodInfo:
            utils.append(line)
    
    if options.designer: 
        for key in sorted(hiddenUtils.iterkeys()):
            methodInfo = hiddenUtils[key]
            for line in methodInfo:
                utils.append(line)
    
    utils.append('</TABLE><HR></BODY></HTML>')
          
    if len(utils) > 2:
        file = open(cwd +'\\' +'Utils.html', 'w')
        file.writelines(utils)
        file.close() 
    
    createIndexPage(createdFiles)
     
	 

def printUsage():
    print '''---------------------------------------------------------------------------------------------------  
    Name: DocCreator.py
    
    Description:
     This script will generate HTML API documentation for the TP API. 
    
    Command:
     python DocCreator.py -v <Version Information> | -d <Print designer level docs>

    
    Command options:
     -v   --version     Version of TP API that the created docs apply to. This is 
                         used in the header of the page. 
    
     -d   --designer    Include hidden methods in the ouput docs. 
---------------------------------------------------------------------------------------------------'''
    sys.exit(' ')


'''
    Parse in the command line arguments
'''   
try:
    parser = OptionParser(conflict_handler="resolve")
    parser.add_option("-v", "--version", dest="version",
                      help="TP API Version", metavar="VERSION")
    
    parser.add_option("-d", "--designer", action="store_true", dest="designer",
                     default=False, help="Print the doc for designer level")
    
    parser.add_option("-h", "--help", action="store_true", dest="help",
                     default=False, help="Prints the usage of the script")
    
    (options,args) = parser.parse_args()
except:
    traceback.print_exc(file=sys.stdout)
    printUsage() 


#-------------------------------
if __name__ == "__main__":
    main()
