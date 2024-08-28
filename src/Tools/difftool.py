"""
Compare two teckpacks using a swing GUI

Paul Smith, 2012

"""

from javax.swing import JScrollPane, JSplitPane, JPanel, JComboBox, JLabel, JButton, JFrame, BoxLayout, GroupLayout, JTextField,JTextArea
from java.awt import GridLayout, BorderLayout
from java.awt.event import ActionListener

import TPAPI 
   
class Example(JFrame):

    version = '0.1'
    
    def __init__(self):
        super(Example, self).__init__()
        self.initUI()

    # handle events for all combo boxes
    class Listener(ActionListener):
        chosen = {}
        def __init__(self, choice, default, lbl):
            self.choice = choice
            self.lbl = lbl
            if choice is not None:
                self.chosen[choice] = default

        def actionPerformed(self, event):
            source = event.getSource()
            val = source.getSelectedItem()
            self.chosen[self.choice] = val
            if val == 'Server':
                self.lbl.text = 'Enter name or IP address of server'
            elif val=='XML file':
                self.lbl.text = 'Enter path to find XML files'
            else:
                self.lbl.text = 'Enter path to find .tpi files'
                

        def getChoices(self):
            return self.chosen

    def initUI(self):
        self.setTitle("TPAPI techpack diff tool. Ver "+self.version)#frame = JFrame("TPAPI techpack diff tool. Ver "+self.version)
        self.setSize(300, 300)
        self.setLayout(BorderLayout())
        
        splitPane = JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        
        self.o_panel = JPanel(GridLayout(6,2,15,15))
        #self.o_panel.setLayout(BoxLayout(self.o_panel, BoxLayout.PAGE_AXIS))
        self.n_panel = JPanel(GridLayout(6,2,15,15))
        
        self.o_l0 = JLabel("Older", JLabel.RIGHT)
        self.o_l1 = JLabel("Techpack")
        self.n_l0 = JLabel("Newer", JLabel.RIGHT)
        self.n_l1 = JLabel("Techpack")
        
        self.o_panel.add(self.o_l0)
        self.n_panel.add(self.n_l0)
        self.o_panel.add(self.o_l1)
        self.n_panel.add(self.n_l1)
 
        source_list = ('Server','XML file','.tpi file')
        
        self.o_l2 = JLabel("Older source :", JLabel.RIGHT)
        self.n_l2 = JLabel("Newer source :", JLabel.RIGHT)

        self.o_panel.add(self.o_l2)
        self.n_panel.add(self.n_l2)
        # created them early becuase they are needed by the combo boxes
        self.o_l3 = JLabel("From source not selected", JLabel.RIGHT)
        self.n_l3 = JLabel("To source not seleceted", JLabel.RIGHT)
        
        self.o_cb1 = JComboBox(source_list)
        self.o_cb1.addActionListener(self.Listener('From_source','Server', self.o_l3)) 
        self.n_cb1 = JComboBox(source_list)
        self.n_cb1.addActionListener(self.Listener('To_source','Server', self.n_l3)) 
        
        self.o_panel.add(self.o_cb1)
        self.n_panel.add(self.n_cb1)
        
        self.o_panel.add(self.o_l3)
        self.n_panel.add(self.n_l3)

        self.o_text = JTextField( actionPerformed = self.o_enterPressed ); 
        self.o_panel.add(self.o_text)
        self.n_text = JTextField( actionPerformed = self.n_enterPressed ); 
        self.n_panel.add(self.n_text)

        self.o_cb2 = JComboBox()
        self.n_cb2 = JComboBox()

        label = JLabel('Select Techpack to compare from', JLabel.RIGHT)
        self.o_panel.add(label)
        label = JLabel('Select Techpack to compare to', JLabel.RIGHT)
        self.n_panel.add(label)
        
        self.o_panel.add(self.o_cb2)
        self.n_panel.add(self.n_cb2)
                
        self.button = JButton('Compare',actionPerformed=self.compareTP)
        self.label = JTextArea(6,80)
        self.label.text = '''Nothing compared yet!\n\n\n'''  

        self.o_panel.add(self.button)
        self.n_panel.add(self.label)

        splitPane.setLeftComponent(self.o_panel);
        splitPane.setRightComponent(self.n_panel);
        splitPane.setDividerLocation(500);       
        
        self.add(splitPane)
        
        self.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE)
        self.pack()
        self.setVisible(True)

    def compareTP(self, e):
        self.label.text = 'Starting comparison. Please be patient.'
        text = self.o_text.getText()
        val =  self.o_cb2.getSelectedItem()
        source = self.o_cb1.getSelectedItem()
        # load the from techpack.
        if source == 'Server':
            tpo = TPAPI.TechPackVersion(val)
            tpo.getPropertiesFromServer(text)
        elif source == 'XML file':
            tpo = TPAPI.TechPackVersion('unknown:((0))')
            inputfile = text+'/'+val
            tpo.getPropertiesFromXML(filename = inputfile)
        elif source == '.tpi file':
            tpo = TPAPI.TechPackVersion('unknown:((0))')
            inputfile = text+'/'+val
            tpo.getPropertiesFromTPI(filename = inputfile)
        else:
            raise 'Insufficient values selected to determine source techpack'
            
        tpn = TPAPI.TechPackVersion('unknown:((1))')
        text = self.n_text.getText()
        val =  self.n_cb2.getSelectedItem()
        source = self.n_cb1.getSelectedItem()
        # load the from techpack.
        if source == 'Server':
            tpn = TPAPI.TechPackVersion(val)
            tpn.getPropertiesFromServer(text)
        elif source == 'XML file':
            inputfile = text+'/'+val
            tpn.getPropertiesFromXML(filename = inputfile)
        elif source == '.tpi file':
            inputfile = text+'/'+val
            tpn.getPropertiesFromTPI(filename = inputfile)
        else:
            raise 'Insufficient values selected to determine target techpack'
        delta = tpo.difference(tpn)
        self.label.text = delta.toString()            
    
    def enterPressed(self, source):
        # What options have been selected from the combo boxes?
        choices = self.Listener(None, None, None).getChoices()
        # which input box are we dealing with?
        if source: # dealing with source inputs 
            val = choices.get('From_source')
            text = self.o_text.getText()
        else: # dealing with dest inputs
            val = choices.get('To_source')
            text = self.n_text.getText()

        if val == 'unset':
            # update status bar with 'no source selected'
            return
        
        if val == 'Server': 
            # text should refer to the name or IP address of a server 
            tplist = getServerList(text)
        if val == 'XML file': 
            # text should refer to the directory containing XML files
            tplist = getXMLList(text)
        if val == '.tpi file': 
            # text should refer to the directory containing XML files
            tplist = gettpiList(text)
                        
        if source:
            cb = self.o_cb2
        else:
            cb = self.n_cb2
        cb.removeAllItems()
        for item in tplist:
            cb.addItem(item)
            

    def o_enterPressed(self, event): 
        self.enterPressed(True)
        
    def n_enterPressed(self, event): 
        self.enterPressed(False)
        
#' get list of techpacks installed on server '+server
def getServerList(server):
    tplist = []
    try: 
        tpvs = TPAPI.getTechPackVersions(server)        
        #exclude non standard TP's
        for tp in sorted(tpvs):
            # we are only interested in tech packs with names like abcxyz:((nnn))
            if tp.endswith('))'):
                tplist.append(tp)
    except:      
        tplist.append('No techpacks available')      
    return tplist   
 
#' get list of techpack xml files located here.
def getXMLList(path):
    tplist = []
    try:
        import os
        for files in sorted(os.listdir(path)):
            if files.upper().endswith('.XML'):
                tplist.append(files)
    except: 
        tplist.append('No techpack XML files found')      
    return tplist   

#' get list of techpack xml files located here.
def gettpiList(path):
    tplist = []
    try:
        import os
        for files in os.listdir(path):
            if files.upper().endswith('.TPI'):
                tplist.append(files)
    except: 
        tplist.append('No techpack .tpi files found')      
    return tplist   
       
       
       
if __name__ == '__main__':
    #RadioButtonExample()            
    Example()
    