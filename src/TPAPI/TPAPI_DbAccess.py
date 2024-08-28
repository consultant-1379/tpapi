'''

Created on 20 Jan 2012
@author: esmipau

Provides database access functions. 
Typical usage:
        with TPAPI.DbAccess(server,'dwhrep') as crsr:
            crsr.execute("SELECT TYPENAME from dwhrep.MeasurementType where VERSIONID =?", (self.versionID,))
            self.factTables = TPAPI.rowToList(crsr.fetchall())
 
not obvious stuff:
This module caches connections between calls, only actually closing them if a different server is selected.
To prevent leaving open sessions dangling a shutdown task is registered to be called when this module is garbage collected.

gotcha's:
When executing sql using the 'with' statement, be careful about calling another method that uses 'with' as the cursor
closed by the exit clause will be the last opened one. 

The getStats() method might be useful for testing that opens match closes etc.
'''
import sys
import logging
import collections
from com.ziclix.python.sql import zxJDBC


class DbAccess(object):
    '''Class for managing ENIQ Database Access '''
    serverAddr = ''
    dbname = ''
    # record some stats
    initCount = 0
    poolHitCount = 0
    connectCount = 0
    disconnectCount =0
    # by default, we expect to use the SyBase drivers to access the databases
    dbDriver = "com.sybase.jdbc3.jdbc.SybDriver"
    # dictionary of supported connections
    dbDict = collections.defaultdict(dict)
    dbDict['dwhdb']  = {'port': ':2640/dwhdb',  'uid': 'dc',     'pid':'dc',    'cnxn': None, 'crsr':[]} 
    dbDict['dwhrep'] = {'port': ':2641/dwhrep', 'uid': 'dwhrep', 'pid':'dwhrep','cnxn': None, 'crsr':[]} 
    dbDict['etlrep'] = {'port': ':2641/etlrep', 'uid': 'etlrep', 'pid':'etlrep','cnxn': None, 'crsr':[]} 
    dbDict['DBA']    = {'port': ':2641/dwhrep', 'uid': 'dba',    'pid':'dba',   'cnxn': None, 'crsr':[]} 
    
    
    def __init__(self, serverAddr, dbname, dbDriver=None):
        ''' Initialise a dbaccess object
         serverAddr is the pingable address of the server hosting the database
         dbname is the name of the database to conect to. Supported values are dwhdb, repdb, etlrep and DBA          
        '''
        
        self.logger = logging.getLogger('TPAPI.DbAccess')
        DbAccess.initCount += 1
        
        if dbname not in DbAccess.dbDict:
            self.logger.error("attempt to connect to unrecognised type of database:"+dbname)
            raise Exception ("attempt to connect to unknown type of database"+dbname)

        self.dbname=dbname
        if DbAccess.serverAddr != serverAddr:
            self.logger.info("Connecting to server "+serverAddr)
            # clean up any old connections
            self._closeConnection()
            DbAccess.serverAddr = serverAddr

        if DbAccess.dbDict[dbname]['cnxn'] is None or DbAccess.dbDict[self.dbname]['cnxn'].closed:
            self._connect()
        else:                 
            DbAccess.poolHitCount += 1
           
            
    def __enter__(self):
        '''returns self.getCursor()'''
        return self.getCursor()
        
    def __exit__(self, Type, Value, tb):
        '''exit the db connection'''
        try: 
            DbAccess.dbDict[self.dbname]['cnxn'].commit()
            self.rollback()
            self.closeCursor()
        except:
            pass
        
    def commit(self):
        ''' Commit query '''
        DbAccess.dbDict[self.dbname]['cnxn'].commit()
        
    
    def rollback(self):
        ''' rollback to the start of any pending transaction '''
        DbAccess.dbDict[self.dbname]['cnxn'].rollback()  
    
    def getConnection(self):
        ''' get connection to db '''
        if DbAccess.dbDict[self.dbname]['cnxn'] is None or DbAccess.dbDict[self.dbname]['cnxn'].closed: 
            self._connect()
        return DbAccess.dbDict[self.dbname]['cnxn']

    def getCursor(self):
        ''' return a dynamic cursor to the db '''
        # open a new cursor for this connection (even if some already exist)
        # this works if usage is a calls b, b calls c
        # if a calls b then c and frees c then continues to use b, confusion arises 
        crsr = DbAccess.dbDict[self.dbname]['cnxn'].cursor(1)
        # add it to the end of the list 
        DbAccess.dbDict[self.dbname]['crsr'].append(crsr)
       
        return crsr 

                
    def closeCursor(self):
        ''' try and close the last open cursor'''
        try:
            crsr = DbAccess.dbDict[self.dbname]['crsr'].pop()  
            crsr.close()            
        except:
            self.logger.info("Problem encountered closing cursor", exc_info=1)
            pass
        return
    
     
    def _closeConnection(self):
        ''' close all open cursors and connections''' 
        try:
            DbAccess.dbDict[self.dbname]['cnxn'].close()
            #self.logger.info('Successfully Closed connection to ' + DbAccess.serverAddr)
        except:
            pass
        DbAccess.disconnectCount +=1


    def _connect(self):
        '''connect to the database'''
        cnxn = DbAccess.dbDict[self.dbname]['cnxn']
        if cnxn is None or cnxn.closed:
            DbAccess.connectCount += 1
            try:  
                cnxnStr =  "jdbc:sybase:Tds:" + DbAccess.serverAddr+DbAccess.dbDict[self.dbname]['port']   
                cnxn = zxJDBC.connect(cnxnStr, DbAccess.dbDict[self.dbname]['uid'], DbAccess.dbDict[self.dbname]['pid'], DbAccess.dbDriver)
                self.logger.info('Successfully Connected to ' + DbAccess.serverAddr)
            except zxJDBC.InterfaceError:
                print 'Failed to connect to db '+self.dbname+' on server '+DbAccess.serverAddr+" using "+cnxnStr, sys.exc_info()
                print 'Interface Error encountered. Please check path to connection jar is correct'
                raise
            except zxJDBC.DatabaseError:
                print 'Failed to connect to db '+self.dbname+' on server '+DbAccess.serverAddr+" using "+cnxnStr, sys.exc_info()
                print 'Database Error encountered. Please check database is operating correctly.'
                raise                 
            except:
                self.logger.error('Failed to connect to db '+self.dbname+' on server '+DbAccess.serverAddr+" using "+cnxnStr, exc_info=1)
                print 'Failed to connect to db '+self.dbname+' on server '+DbAccess.serverAddr+" using "+cnxnStr, sys.exc_info()
                raise 
        DbAccess.dbDict[self.dbname]['cnxn'] = cnxn
        return cnxn
                   
    def __del__(self):
        ''' close any open cursors associated with the connection, then the connection itself '''
        self.closeCursor()
        #DbAccess.disconnectCount += 1
            

    def getTables(self,hint):
        ''' get the list of tables in this database that match the hint
        e.g. to get all BSS tables use the hint 'DC_E_BSS_%'
             to get all tables, use the hint '%' or none'''
        return self._mygetTables(hint,('TABLE',))
        
    def getViews(self,hint):
        ''' get the list of views in this database that match the hint
        e.g. to get all BSS views use the hint 'DC_E_BSS_%'
             to get all views, use the hint '%' or none'''
        return self._mygetTables(hint,('VIEW',))
        
    def _mygetTables(self, hint, types):
        tableList = {}
        crsr = self.getCursor() # get a staatic cursor
        try : 
            crsr.tables(None, None, hint, types)
            for a in crsr.fetchall():
                tableList.add(a[3])
        except:
            err =  sys.exc_info()
            raise Exception('Failed to get crsr.tables on '+self.dbname+' on server '+DbAccess.serverAddr+'\nReason given is ',err)

        finally:
            self.closeCursor()
            
        return tableList    
        
    @staticmethod 
    def getStats():
        ''' return a string with DbAccess stats in it '''
        outStr  = "DbAccess init count :"
        outStr += str(DbAccess.initCount)
        outStr += ", pool Hits :"
        outStr += str(DbAccess.poolHitCount)
        outStr += ", connects :"
        outStr += str(DbAccess.connectCount)
        outStr += ", disconnects :"
        outStr += str(DbAccess.disconnectCount)
        return outStr


def shutdown():
        ''' clean up on application exit '''
        try:
            for conn in DbAccess.dbDict.keys:
                if conn['cnxn'] is not None and not conn['cnxn'].closed:
                    for crsr in conn['crsr']:
                        try: 
                            crsr.close()
                        except:
                            pass
                    try: 
                        conn['cnxn'].close()
                    except:
                        pass
        except:
            pass

         
# register a shutdown task to tidy up on application exit
import atexit
atexit.register(shutdown)
        
