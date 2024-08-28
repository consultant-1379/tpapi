# import TPAPI

#change for git testing


class Delta(object):
    '''Class for recording and reporting techpack delta information'''
    
    def __init__(self,originalVersionID,newVersionID):
        '''Initialised using orginalVersionID and newVersionID of the techpacks to be diffed
        
        Instance Variables:
           self.originalVersionID:
                Description: versionID of the previous or base TP version. eg DC_E_BSS:((100)).
                Type:String
                
           self.newVersionID:
                Description: versionID of the newest TP version. eg DC_E_BSS:((101)).
                Type:String
                
           self.changes:
                Description: Dictionary containing the changes
                Type:Dictionary
                Keys:
                    String Location of the change eg. 'Techpack=DC_S_TEST,VersionID=DC_S_TEST:((22)),Interface=<deleted>INTF_DC_E_STEVE,Version =<deleted>((1)),versioning=<deleted>RSTATE'
                    SubKeys:
                            OLDVAL
                            NEWVAL
                            
            self.deltaTPV:
                Description: TechPack Version object with the new (not deleted) content between the TPs.
                Type: TechPackVersion
                
            self.numchanges:
                Description: Number of recorded changes
                Type: int
        
        '''
        
                
        self.originalVersionID = originalVersionID # base version of the tp
        self.newVersionID = newVersionID # upgraded versionid of the tp
        self.changes = {}# dictionary of changes including new and old values
        self.stack = [] # used to record where the changes have occured
        self.deltaTPV = '' # Delta Techpack Version object, is added to the delta object during a diff.
        self.numchanges = 0

    def _getNumChanges(self):
        '''Returns the number of changes recorded in the delta 
        
        Returns:
                self.numchanges
        
        '''
        return self.numchanges

    def _addChange(self,stack,newVal=None,oldVal=None):
        '''Adds a change to the change dictionary, using a stack, delta & original values.'''
        self.numchanges += 1
        strg =  ",".join(stack)
        if strg not in self.changes:
            self.changes[strg] = {'OLDVAL':oldVal,'NEWVAL':newVal}

    def toString(self):
        '''Converts the delta found to string output
        
        Returns:
                string of the delta recorded
        
        '''
        deltaString = ''
        
        for change in sorted(self.changes.iterkeys()):
            deltaString += change
            for item in self.changes[change]:
                deltaString += ';'+item + "=" + str(self.changes[change][item])
            deltaString += '\n'
        return deltaString          

    
    def toXML(self):
        ''' Not implemented - executes self.toString() method
        
        Returns:
                self.toString()
        
        '''
        return self.toString()
        
    def deltaTPVtoXML(self):
        return self.deltaTPV.toXML()
    
    
    
