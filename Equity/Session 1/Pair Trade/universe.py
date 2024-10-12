# importing ibraries for app visuals 
from ipywidgets import Layout, Button, HTML, DatePicker, VBox, HBox, Text, Tab, Box, Dropdown, Textarea
from bqwidgets import TickerAutoComplete

# default caption styling 
caption = '<h3>{h}</h3>'

# default input boxes layout
_LAY = {'width':'130px'}
_LAY_WID = {'width': '180px'}

# default configurations for the Universe section 
universe_config = {
    'Index': {
        'active':True,
        'startup':True,
        'value':'BCOM Index',
    },
    'List': {
        'active':True,
        'startup':False,
        'value':'NG1 Comdty \n CL1 Comdty\n CO1 Comdty\n C 1 Comdty\n S 1 Comdty\n QS1 Comdty\n XB1 Comdty\n W 1 Comdty\n C 1 Comdty\n FN1 Comdty',
    },
}

class UniversePicker:   
    '''
    UniversePicker class for dynamic Universe selection (Index/List)
    '''
    
    def __init__(self, layout=None):
        layout = {'layout': layout} if layout else {}
        # load the default configuration 
        self.cfg = universe_config
        # create a dictionary of widgets to ease display
        self.widgets = dict()
        # build the UI box
        obj_lst = self.build_ui()
        self.box = VBox(obj_lst, **layout)
      
    def show(self):
        return self.box

    def get_universe(self):
        """
        Retrieve user inputs from universe selection 
        under the form of a dictionary. 
        """
        
        univ = self.widgets['univ_type'].value
        value = self.widgets['univ_value'].children[0]
        if univ == 'Index':  
            element = [value.value.split(':')[0]]
        if univ == 'List': 
            element = value.value.split('\n')
    
        return {'type':univ, 'value':element}

    def build_ui(self):
        """
        Widgets for picking a universe.
        """
        
        # create a label for universe selection
        self.widgets['label'] = HTML(caption.format(h='Universe selection'))
        # dropdown universe type selector
        univ_type_options = [x for x in self.cfg.keys() if self.cfg[x]['active']]
        univ_type_default = [x for x in self.cfg.keys() if self.cfg[x]['startup']][0]
        self.widgets['univ_type'] = Dropdown(options=univ_type_options, value=univ_type_default , layout=_LAY)
        self.widgets['univ_type'].observe(self._on_univ_type_change, 'value')
        
        # objects for the universe selectors
        widget_layout = {'min_width':'180px'}
        self.widgets['univ_value'] = VBox(layout=widget_layout)

        # Call the event handler to show the default widget.
        self._on_univ_type_change()
        
        # final UI for universe picker
        output = VBox([self.widgets['label'], 
                      HBox([self.widgets['univ_type'], self.widgets['univ_value']])])
        return [output]

    def _on_univ_type_change(self, *args, **kwargs):
        """
        Updates widget according to the universe type selected by user 
        """
        
        # Show different widgets according to the universe type user selected.
        univ = self.widgets['univ_type'].value
        # fetch the associated configuration
        cfg_ = self.cfg[univ]
        
        # assign the relevant widget output to univ_value
        if univ == 'Index':
            element = TickerAutoComplete(value=cfg_['value'], yellow_keys=['Index'], layout=_LAY_WID)
            
        elif univ == 'List':
            element = Textarea(value=cfg_['value'], rows=4, placeholder='Place one ticker per line', layout=_LAY_WID)
            
        self.widgets['univ_value'].children = [element]