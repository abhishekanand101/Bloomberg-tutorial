import pandas as pd
# import bqport
from ipywidgets import Dropdown, Layout, Textarea, HBox, ToggleButton, Checkbox, RadioButtons, HTML, Box, VBox
from bqwidgets import TickerAutoComplete, DateRangeSelector
from collections import OrderedDict
from datetime import datetime, timedelta

class UniversePicker:
    def __init__(self, default=None, bq=None, layout=None):
        """Widgets for picking a universe. Index members and portfolio members are supported."""
        self.bq = bq
        self._dropdown_type = Dropdown(options=['Index', 'Portfolio', 'List'], value=default['type'])
        self._dropdown_port = Dropdown()
        self._ac_index = TickerAutoComplete(yellow_keys=['Index'], value=default['value'])
        self._txt_custom = Textarea(placeholder='Place one ticker per line')
        
        layout = {'layout': layout} if layout else {}
        self._box = HBox([self._dropdown_type], **layout)
        
        self._dropdown_type.observe(self._on_type_change, 'value')
        
        # Call the event handler to show the default widget.
        self._on_type_change()

    def show(self):
        return self._box

    @property
    def universe(self):
        """Get currently selected universe as a BQL item."""
        univ = self._dropdown_type.value
        if univ == 'Index':
            if self._ac_index.value:
                #return self.bq.univ.members(self._ac_index.value.split(':')[0])
                return self._ac_index.value.split(':')[0]
            else:
                return None

        elif univ == 'Portfolio':
            if self._dropdown_port.value:
                return self.bq.univ.members(self._dropdown_port.value)
            else:
                return None

        elif univ == 'File':
            if self._txt_custom.value:
                f = open(self._txt_custom.value)
                tickers = f.readlines()
                f.close()
                securities = [t.strip() for t in tickers]
                return self.bq.univ.list(securities)
            else:
                return None

        elif univ == 'List':
            if self._txt_custom.value:
                # Drop any line containing garbage character
                tickers = [c.strip() for c in self._txt_custom.value.splitlines() if c.isprintable()]
                return self.bq.univ.list(tickers)
            else:
                return None

    def _on_type_change(self, *args, **kwargs):
        # Show different widgets according to the universe type user selected.
        univ = self._dropdown_type.value
        if univ == 'Index':
            self._box.children = [self._dropdown_type, self._ac_index]
            
#         elif univ == 'Portfolio':
#             self._box.children = [self._dropdown_type, self._dropdown_port]
#             portfolios = bqport.list_portfolios()
#             portfolios = sorted([(p['name'], p['id']) for p in portfolios])
#             self._dropdown_port.options = portfolios
            
        elif univ == 'File':
            self._txt_custom.placeholder = 'file name'
            self._box.children = [self._dropdown_type, self._txt_custom]
            
        elif univ == 'List':
            self._txt_custom.placeholder = 'Place one ticker per line'
            self._box.children = [self._dropdown_type, self._txt_custom]
            
            

class FactorPicker:
    def __init__(self, factors, default_composite, layout=None):
        """Widgets for picking factors as composite factor."""
        # Apply the score function, and sort the factors alphabetically
        self._factors = sorted([(k, v) for k, v in factors.items()])
        self._toggles = []
        for k, v in self._factors:
            toggle = ToggleButton(description=k, value=k in default_composite)
            toggle.observe(self._on_toggle_selected, 'value')
            self._toggles.append(toggle)
        
        self._html = HTML()
        
        # Default layout: flex_flow='row wrap'
        layout = layout or Layout()
        if not layout.flex_flow:
            layout.flex_flow = 'row wrap'
        
        toggles_box = Box(self._toggles, layout=layout)
        self._box = VBox([toggles_box, self._html])
        
        # Call the event handler to show the default selected.
        self._on_toggle_selected()

    def show(self):
        return self._box

    @property
    def bql_items(self):
        """Get currently selected factors as a dict."""
        items = OrderedDict([self._factors[i] for i, toggle in enumerate(self._toggles) if toggle.value])
        return items
    
    def _on_toggle_selected(self, *args):
        for t in self._toggles:
            if t.value:
                t.icon='check'
            else:
                t.icon='uncheck'
        selected = [t.description for t in self._toggles if t.value]
        if selected:
            self._html.value = 'Currently selected: ' + ', '.join(selected)
        else:
            self._html.value = 'No factor selected.'
            
            
            
class DisplaySettingPicker:
    def __init__(self, default_settings, layout=None):
        """Widgets for picking factor settings"""
        self._settings = default_settings
        self._checkbox = []
        for k, v in self._settings:
            checkbox = Checkbox(description=k, value=v)
            checkbox.observe(self._on_toggle_checkbox, 'value')
            self._checkbox.append(checkbox)
            
        self._html = HTML()
        
        # Default layout: flex_flow='row wrap'
        layout = layout or Layout()
        if not layout.flex_flow:
            layout.flex_flow = 'row wrap'
            
        checkbox_box = VBox(self._checkbox, layout=layout)
        self._box = VBox([checkbox_box, self._html])
        
        self._on_toggle_checkbox()
        
    def show(self):
        return self._box
    
    @property
    def get_selection(self):
        """Get selected settings as a dict."""
        items = OrderedDict([self._settings[i] for i, checkbox in enumerate(self._checkbox) if checkbox.value])
        return list(items.keys())
    
    def _on_toggle_checkbox(self, *args):
        selected = [c.description for c in self._checkbox if c.value]
        if selected:
            self._html.value = 'Backtest will run on: ' + ', '.join(selected)
        else:
            self._html.value = 'No backtest setting defined.'
            
            
            
class SettingPicker:
    def __init__(self, default_params, layout=None):
        """Widgets for picking factor settings"""
        self._settings = default_params
        self.date_selector = DateRangeSelector(start='20140101', end=datetime.today(),)# layout={'min_width':'400px'})
        self.date_selector.intsel.selected = pd.to_datetime([(datetime.today() - timedelta(days=365)).strftime('%Y%m%d'), datetime.today().strftime('%Y%m%d')])
        self._radio = radio = RadioButtons(description='Frequency', options=['Monthly','Quarterly','Yearly'], value=self._settings['freq'])
        self._ccy = Dropdown(description='Currency', value=self._settings['currency'], options=['USD','EUR','GBP','SGD','MYR','IDR','PHP'])
        
        self._html = HTML()
        
        # Default layout: flex_flow='row wrap'
        layout = layout or Layout()
        if not layout.flex_flow:
            layout.flex_flow = 'row wrap'
               
        radio_box = VBox([self.date_selector, self._radio, self._ccy], layout=layout)
        self._box = VBox([radio_box, self._html])
        
    def show(self):
        return self._box
    
    @property
    def get_selection(self):
        """Get selected settings as a dict."""
        items = {
            'start_date': pd.to_datetime(self.date_selector.intsel.selected[0]),#.astype(datetime),
            'end_date'  : pd.to_datetime(self.date_selector.intsel.selected[1]),#.astype(datetime),
            'freq'      : self._radio.value,
            'currency'  : self._ccy.value,
        }
        return items
    