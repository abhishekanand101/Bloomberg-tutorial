import numpy as np
import pandas as pd
import ipywidgets
import bqwidgets
import logging
# from bqplot import LinearScale, OrdinalScale, DateScale, ColorScale, GridHeatMap, Lines, Bars, Scatter, Axis, ColorAxis, Figure, Tooltip
from model import DataModel
from logwidget import LogWidget, LogWidgetAdapter, LogWidgetHandler
from datetime import datetime, timedelta
# import bqviz as bqv
from IPython.display import display
from matplotlib.cm import get_cmap
from matplotlib.colors import rgb2hex
from constants import *
from utils import *
# import bqport
import heatMapHelper
import DataframeStyler
import re


# Widget to display the logs
_LOG_WIDGET = LogWidget(
    layout={'border': '1px solid dimgray', 'margin': '10px'})
_LOADING_SPIN = """<i class="fa fa-spinner fa-spin fa-2x fa-fw"></i>"""

# Handler to sink the logs to the widget
_HANDLER = LogWidgetHandler(_LOG_WIDGET)
_FORMATTER = logging.Formatter('%(asctime)s - %(message)s', '%H:%M:%S')
_HANDLER.setFormatter(_FORMATTER)

# Define app logger and add widget handler
_LOGGER = logging.getLogger('CreditApp')
_LOGGER.addHandler(_HANDLER)
_LOGGER.setLevel(logging.DEBUG)

HMAP, CLEAN_DATA, DATA_DISPLAY = None, None, None
HH = heatMapHelper.HeatMapHelper()
STYLER = DataframeStyler.Styler()

class CreditApp():
    """ Class to control the User Interface
    """

    def __init__(self):
        self.field = []
        # application controls
        self.tab_screener_box = None
        self.tab_sprd_anls_box = None
        self.ticker = ''
        self.lookback = 0
        self.periodicity = ''
        self.sprd_level = 0
        self.sprd_side = ''
        self.config = None
        # self.ptf_id = ''
        self.ptf_comparison = False
        self.ptf_only = False
        # UI Component
        self.button_set_config = None
        self.button_run = None
        self.button_config = None
        self.button_ptf = None
        # self.button_compare = None
        self.widgets = dict()
        self.button_HM_drilldown = None
        # Heatmap toggle button
        self.heatmap_controls = ipywidgets.ToggleButtons(options=['All', 'Financials', 'Ex-Financials'])
        self.heatmap_drilldown = None
        # Model
        self.data_model = None

    def show(self):
        """ Display user interface
        """
        ui = self.build_ui()
        self.build_config()
        display(ui)
        _LOGGER.info('Select the index and click Run to start.')


    def build_ui(self):
        """ Build the elements of the UI
        """
        self.widgets['app_title'] = ipywidgets.HTML("""<h1>Credit Screening Tool</h1>""")
        self.widgets['app_controls'] = self.build_app_controls()
        self.widgets['app_config'] = ipywidgets.HBox()

        # Create tabs for the output. 
        # One tab for the screening based on the score screening
        # One tab for the spread analysis (heatmap and details) 
        main_tab = ipywidgets.Tab(layout={'margin': '10px', 'overflow_x': 'auto'})
        main_layout = ipywidgets.Layout(flex_flow='row wrap', min_width='800px')

        # define tabs
        self.tab_screener_box = ipywidgets.Box(layout=main_layout)
        self.tab_sprd_anls_box = ipywidgets.Box(layout=main_layout)

        tab_children = [self.tab_screener_box, self.tab_sprd_anls_box]
        tab_titles = ['Screener', 'Spread Analysis']

        # create the tab titles dynamically
        main_tab.children = tab_children
        for k,v in enumerate(tab_titles):
            main_tab.set_title(k, v)

        self.widgets['app_output'] = main_tab

        ui = ipywidgets.VBox([
            self.widgets['app_title'],
            self.widgets['app_controls'],
            self.widgets['app_config'],
            self.widgets['app_output'],
            _LOG_WIDGET.get_widget()
            ],
                             layout={
                                 'overflow_x': 'auto',
                                 'overflow_y': 'auto'
                                 }
                             )
        return ui

    def build_app_controls(self):
        """ Build the main controls of the app
        """
        self.widgets['ticker'] = bqwidgets.TickerAutoComplete(yellow_keys=['index'], 
                                                              description='Universe:', 
                                                              placeholder='Universe',
                                                              value='EMUSTRUU Index')
        self.widgets['periodicity'] = ipywidgets.Dropdown(options=PERIODICITY,
                                                          placeholder='Periodicity',
                                                          description='Periodicity:',
                                                          layout={'width': '200px'})
        self.widgets['lookback_period'] = ipywidgets.IntText(value=3,
                                                             description='Lookback:',
                                                             layout={'width': '150px'})

        self.button_run = ipywidgets.Button(description='Run', 
                                            button_style='info', 
                                            icon='fa_play')
        self.button_run.on_click(self.refresh_data)

        self.button_config = ipywidgets.Button(description='Load Config',
                                               button_style='success',
                                               icon='fa_play')
        self.button_config.on_click(self.show_config)

        self.widgets['spread_title'] = ipywidgets.HTML("<span style='text-align:center;margin-left:20px;margin-right:5px'>G-Spread</span>")
        self.widgets['spread_side'] = ipywidgets.Dropdown(options=['>', '<', ''], layout={'width':'40px'})
        self.widgets['spread_level'] = ipywidgets.IntText(value=250, layout={'width': '70px'})

        # self.widgets['ptf_id'] = ipywidgets.Dropdown(options=CreditApp.get_portfolio_list(),
        #                                              description='Portfolio ID')
        self.widgets['ptf_comparison'] = ipywidgets.Checkbox(value=False, 
                                                             indent=False,
                                                             layout={'width': '50px'})
        self.button_ptf = ipywidgets.Button(description='Refresh Port',
                                            button_style='info',
                                            icon='fa_play')
        self.button_ptf.on_click(self.refresh_ptf_data)

        self.button_HM_drilldown = ipywidgets.Button(description='Drilldown',
                                                     button_style='info',
                                                     icon='fa_play')

        controls = [
            self.widgets['ticker'],
            self.widgets['periodicity'],
            self.widgets['lookback_period'],
            self.widgets['spread_title'],
            self.widgets['spread_side'],
            self.widgets['spread_level']
        ]
        ptf_controls = [
            # self.widgets['ptf_id'],
            self.button_ptf,
            self.button_config,
            self.button_run
            # ,
            # self.button_compare
        ]

        return ipywidgets.VBox(
            [ipywidgets.HBox(controls, layout={'overflow_x':'auto'}),
             ipywidgets.HBox(ptf_controls, layout={'overflow_x':'auto'})],
            layout={'overflow_x': 'auto'}
        )

    def set_app_controls(self):
        """ Method to set all the application controls to send to the model
        """
        self.ticker = self.widgets['ticker'].value \
            # if self.widgets['ticker'].value != '' \
            #     else self.get_ptf_id(self.widgets['ptf_id'].value)
        self.lookback = int(self.widgets['lookback_period'].value)
        self.periodicity = get_bql_fpt(self.widgets['periodicity'].value)
        self.ptf_comparison = self.widgets['ptf_comparison'].value
        # self.ptf_id = self.widgets['ptf_id'].value
        self.ptf_only = self.widgets['ticker'].value == ''
        self.sprd_level = self.widgets['spread_level'].value
        self.sprd_side = self.widgets['spread_side'].value
        self.config = self.get_config()

    def refresh_data(self, *args, **kwargs):
        """ Method to refresh the model
        """
        _LOGGER.info('Refreshing Data')
        try:
            self.set_app_controls()
            self.data_model = DataModel(ticker=self.ticker,
                                        lookback_period=self.lookback,
                                        periodicity=self.periodicity,
                                        sprd_level=self.sprd_level,
                                        sprd_side=self.sprd_side,
                                        config=self.config,
                                        ptf_only=self.ptf_only)
            _LOGGER.info('Retrieving data for screening.')
            self.data_model.run()
            self.build_output_screening(self.data_model.data.reset_index())

            # if self.ptf_id != '' and self.ticker != self.get_ptf_id(self.ptf_id):
            #     _LOGGER.info('Retrieving data for portfolio.')
            #     self.data_model.run_ptf(self.ptf_id)
            #     _LOGGER.info('Comparing Index and portfolio')
                # self.run_comparison()
        except Exception as e:
            _LOGGER.error('Error Retrieving data... %s',e)
            
        try: 
            self.refresh_heatmap_data()
        except Exception as e:
            _LOGGER.error('Error building heatmap... %s',e)

    def refresh_heatmap_data(self, *args, **kwargs):
        """ Method to refresh the spread analysis heatmap
        This method should be used after the main screener is run
        """
        _LOGGER.info('Retrieving spread analysis.')
        self.data_model.run_heatmap(self.heatmap_controls.value)
        self.build_output_heatmap(self.data_model.data_heatmap)
        _LOGGER.info('Spread analysis retrieved.')

    def refresh_ptf_data(self, *args, **kwargs):
        """ Method to refresh the portfolio data only
        It avoids user to reload the whole thing if he needs to change portfolio
        """ 
        #stop here
        # self.ptf_id = self.widgets['ptf_id'].value
        # if self.ptf_id != '':
        #     _LOGGER.info('Retrieving data for portfolio.')
        #     self.data_model.run_ptf(self.ptf_id)
        #     _LOGGER.info('Comparing Index and portfolio')
        #     self.run_comparison()

    def build_output_screening(self, df):
        """ Create the output grid widget to display the result of the screening
        """
        _LOGGER.info('Building output table.')
        dgrid = bqwidgets.DataGrid(data=df.round(3))
        dgrid.layout.width = '600px'
        dgrid.observe(self.build_details_ui(), 'selected_row_indices')
        self.tab_screener_box.children = []
        self.widgets['output_grid'] = ipywidgets.VBox([dgrid])
        self.widgets['output_details'] = ipywidgets.HBox()

        self.tab_screener_box.children = \
        [ipywidgets.HBox([
            ipywidgets.VBox([ipywidgets.HTML('<h3>Screening results</h3>'),
                             self.widgets['output_grid'],
                             ipywidgets.HTML('<p>{} results</p>'.format(len(df))),
                             self.build_summary_details(df)
                             ], layout={'width':'600px'}),
            ipywidgets.VBox([self.widgets['output_details']])
        ], layout={'overflow_x':'auto'})]
        _LOGGER.info('Output table built.')

    def build_summary_details(self, df):
        """ Method to generate Summary table
        """
        summary = SUMMARY_SCREEN.format(
            avg_credit_score=df['#credit_score_filtered'].mean(),
            avg_valuation_score=df['#valuation_score_filtered'].mean(),
            nb_bonds=len(df),
            nb_issuer=len(df['#issuer_filtered'].unique())
        )
        return ipywidgets.HTML(summary)

    def build_details_ui(self):
        """ Method to return the observe function put in the datagrid event
        """
        def build_output_details(caller):
            """
            Build the output for security details when clicked
            """
            _LOGGER.info('Building details table.')
            try:
                selected_id = caller['new']
                grid = self.widgets['output_grid'].children[0]
                selected_ticker = grid.data.iloc[selected_id]['ID'].item()
                details_df = self.data_model.get_ticker_details(selected_ticker).round(3)
                name = details_df['#name'].item()
                mapping = self.data_model.config
                scores = mapping['Score'].unique()
                details_body = []
                for score in scores:
                    body = self.generate_details_body(details_df, mapping, score)
                    details_body.append(
                        ipywidgets.HTML(
                            TEMPLATE_DETAILS.format(
                                name=name,
                                score_name=score,
                                body=body,
                                score_value=details_df[score].item()
                            )
                        )
                    )
                self.widgets['output_details'].children = details_body
                _LOGGER.info('Details table built.')
            except Exception as e:
                _LOGGER.error('Error building output details ... %s', e)
        return build_output_details

    def generate_details_body(self, details_df, mapping, score):
        """
        Method to create the details table body with the results from the query
        """
        lines = []
        for fld, _ in mapping[mapping['Score'] == score].iterrows():
            lines.append(
                TEMPLATE_DETAILS_LINE.format(
                    field=fld,
                    current=details_df[mapping.loc[fld]['Current Name']].item(),
                    change=self.get_change_text_value(
                        details_df[mapping.loc[fld]['Change Name']].item(),
                        mapping.loc[fld]['Side'].item()
                    )
                )
            )
        return ''.join(lines)


    def get_change_text_value(self, value, side):
        text_value = 'Neutral'
        if value * side > 0:
            text_value = 'Better'
        elif value * side < 0:
            text_value = 'Worst'
        return text_value

    def build_output_heatmap(self, df):
        """ Method to create the heatmap UI
        """
        self.heatmap_controls.observe(self.refresh_heatmap_data, 'value')
        HH.generate_heatmaps([('OAS breakdown by Credit Rating', df)])
        self.heatmap_drilldown = ipywidgets.VBox()
        self.button_HM_drilldown.on_click(self.generate_heatmap_drilldown)
        self.tab_sprd_anls_box.children = [
            ipywidgets.HBox(
                [
                    self.heatmap_controls,
                    ipywidgets.HBox(
                        [
                            HH.widgets['heatmap_container'],
                            self.button_HM_drilldown
                        ]),
                    self.heatmap_drilldown
                    ], layout={'overflow_x': 'hidden'})]

    def generate_heatmap_drilldown(self, *args, **kwargs):
        """
        Get all the information for the selected buckets of the heatmap
        """
        _LOGGER.info('Generating Heatmap drill down.')
        try:
            selected_selection = HH.get_selected_cells()
            ratings = [r for r, _, _ in selected_selection]
            durations = [d for _, d, _ in selected_selection]

            if ratings is not None and durations is not None:
                _LOGGER.info('Getting drill down data.')
                dd_df = self.data_model.get_heatmap_details(ratings, durations, self.heatmap_controls.value).round(3)
                new_df = dd_df.astype(object).where(dd_df.notnull(), '')
                _LOGGER.info('Drill down retrieved.')
                self.heatmap_drilldown.children = []
                self.heatmap_drilldown.children = [
                    bqwidgets.DataGrid(data=new_df.reset_index(), layout={'width':'1100px', 'height': '500px'}),
                    ipywidgets.HTML('<p>{} results</p>'.format(len(new_df)))
                ]
                _LOGGER.info('Heatmap drill down generated.')
        except Exception as e:
            _LOGGER.error('Error generating drilldown ... %s', e)

    def build_config(self):
        """ Method to get the default config from the excel file
        """
        mapping = pd.read_csv("config.csv", index_col='Field Name')
        for index, row in mapping.iterrows():
            self.field.append(index)
            self.widgets['title_{}'.format(index)] = ipywidgets.HTML("""<p>{}</p>""".format(index))
            self.widgets['weight_{}'.format(index)] = \
                ipywidgets.IntSlider(value=row['Weight'], min=0, max=10)
            self.widgets['side_{}'.format(index)] = \
                ipywidgets.Dropdown(options=SIDE_OPTIONS, value=int(row['Side']))

    def build_config_ui(self):
        """  Build the UI allowing the config change
        """
        fields_area = []
        weight_area = []
        side_area = []

        for fld in self.field:
            fields_area.append(self.widgets['title_{}'.format(fld)])
            weight_area.append(self.widgets['weight_{}'.format(fld)])
            side_area.append(self.widgets['side_{}'.format(fld)])

        config_output = ipywidgets.HBox([
            ipywidgets.VBox(fields_area, layout={'overflow_x':'hidden'}),
            ipywidgets.VBox(weight_area, layout={'overflow_x':'hidden'}),
            ipywidgets.VBox(side_area, layout={'overflow_x':'hidden'})])

        self.button_set_config = ipywidgets.Button(description='Set Config',
                                                   button_style='success',
                                                   icon='fa_play')
        self.button_set_config.on_click(self.set_config)

        config_ui = ipywidgets.VBox([
            ipywidgets.HTML("""<h2>Configuration</h2>"""),
            self.button_set_config,
            config_output
        ], layout={'overflow_x':'hidden'})

        return config_ui

    def show_config(self, *args, **kwargs):
        """ Make the config UI visible
        """
        _LOGGER.info('Loading Config.')
        config_ui = self.build_config_ui()
        self.widgets['app_config'].children = [config_ui]
        _LOGGER.info('Config Loaded.')

    def set_config(self, *args, **kwargs):
        """ Method to hide the config UI
        """
        self.widgets['app_config'].children = []
    
    def get_config(self):
        """ Method to get the config to send to the model
        """
        fld_array = []
        weight_array = []
        side_array = []

        for fld in self.field:
            fld_array.append(fld)
            weight_array.append(self.widgets['weight_{}'.format(fld)].value)
            side_array.append(self.widgets['side_{}'.format(fld)].value)

        config_df = pd.DataFrame(data={ 'Field Name': fld_array, \
            'Weight': weight_array,\
                'Side': side_array}).set_index('Field Name')
        return config_df

    def get_comparison(self, df1, df2):
        """ Compare two dataframes
        """
        df = df1.copy()
        df['Ptf'] = ''
        df.loc[df1.index.intersection(df2.index), 'Ptf'] = 'In'
        return df.reset_index()

    def run_comparison(self, *args, **kwargs):
        """ Refresh Comparison if Ptf data is available
        """
        if self.data_model.data_ptf is not None and self.data_model.data is not None:
            df = self.get_comparison(self.data_model.data, self.data_model.data_ptf)
            dgrid = bqwidgets.DataGrid(data=df)
            dgrid.layout.width = '600px'
            dgrid.observe(self.build_details_ui(), 'selected_row_indices')
            self.widgets['output_grid'].children = [dgrid]

    # def get_portfolio_list():
    #     """ Method to get all porftolios from PRTU
    #     """
    #     # portfolios = bqport.list_portfolios()
    #     portfolios = [(p['name'], p['id']) for p in portfolios]
    #     portfolios.append(('', ''))
    #     return sorted(portfolios)

    def get_ptf_id(self, value):
        if value == '':
            return ''
        return 'U{}'.format(re.search(r'\-(.*)', value, re.IGNORECASE).group(1).replace(':','-'))
