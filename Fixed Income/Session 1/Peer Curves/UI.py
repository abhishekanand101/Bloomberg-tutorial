
import UtilityWidgets
import ipywidgets as widgets
import bqwidgets
import ipydatagrid
import plotly.express as px
import plotly.graph_objects as go
import scatterplot as sc
# import bqviz as bqv
import pandas as pd
import traceback
import os
from IPython.display import display
import bqplot as bqp


class UI():
    def __init__(self,app):
        self.app=app
        logger_layout = {'min_height':'120px', 'max_height':'120px','width':'600px'}
        self.spinner_box = widgets.HBox([])
        self.is_spinner_on=False

        self.DEFAULT_INDEX_STRING = "LUACTRUU Index"

        self.app_logger = UtilityWidgets.ApplicationLogger(max_msgs=60,layout_dict=logger_layout)
        self.app_logger_box_contents = widgets.HBox([self.app_logger.get_widget(), self.spinner_box])

        self.app_logger_box = widgets.Accordion(children=[self.app_logger_box_contents])
        self.app_logger_box.set_title(0, 'Status messages')
        self.app_logger_box.selected_index = None


        self.main_gui = self._construct_main_gui()

        # self.canvas = widgets.VBox([self.main_gui, self.app_logger_box])
        self.canvas = widgets.VBox([self.main_gui])
        self.update_status('Completed Initial Display. Ready for input.')

        self.DEFAULT_DATAGRID_WIDTH = '1022px'
        self.DEFAULT_DATAGRID_HEIGHT='260px'
        self.DEFAULT_DATAGRID_COL_WIDTH = 140
        self.DEFAULT_DATAGRID_INDEX_WIDTH = 100
        self.DEFAULT_DG_COMBINED_COL_WIDTH= 180

        self.DEFAULT_CHART_WIDTH= '1000px'
        # self.DEFAULT_CHART_WIDTH= '100%'

        self.DEFAULT_DATAGRID_INDEX_WIDTH_FUNDAMENTALS = 150
        self.DEFAULT_DATAGRID_COL_WIDTH_FUNDAMENTALS = 160
        # self.DEFAULT_DATAGRID_WIDTH_FUNDAMENTALS = '1460px'
        self.DEFAULT_DATAGRID_WIDTH_FUNDAMENTALS = '100%'
        self.DEFAULT_DATAGRID_HEIGHT_FUNDAMENTALS = '400px'

        self.DEFAULT_DATAGRID_WIDTH_TREND = '1022px'
        # self.DEFAULT_DATAGRID_WIDTH_TREND = '100%'
        self.DEFAULT_DATAGRID_HEIGHT_TREND ='220px'

        self.dict_term_structure_plot_data = dict()
        self.dict_term_structure_dg = dict()
        self.dict_button_click_lookup = dict()

    def _construct_main_gui(self):

        top_items=[]
        gui_items=[]        
        self.input_area=self.__build_input_area()
        # input_area = widgets.Accordion(children=[input_area_contents])
        # input_area.set_title(0, 'Input')


        # top_items.append(input_area)
        self.top_level_summary_area = self.__build_top_level_summary_area()
        # top_items.append(self.top_level_summary_area)

        # top_area = widgets.VBox(top_items)
        # gui_items.append(self.input_area)
        # top_area_with_logger = widgets.HBox([top_area,self.app_logger_box])
        # gui_items.append(top_area)

        self.output_area=self.__build_output_area()
        gui_items.append(self.output_area)
        gui_items.append(self.app_logger_box)

        box = widgets.VBox(gui_items)
        return box

    def __build_input_area(self):
        # gui_items=[]
        top_items=[]
        second_items=[]
        third_items=[]
        
        ticker_input_elt=self._build_ticker_input_elt()
        top_items.append(ticker_input_elt)

        metric_chooser_elt = self.__build_metric_chooser_elt()
        #top_items.append(metric_chooser_elt)
        second_items.append(metric_chooser_elt)

        universe_filtering_elt = self.__build_universe_filtering_elt()
        #second_items.append(universe_filtering_elt)
        third_items.append(universe_filtering_elt)

        sub_or_senior_elt = self._build_sub_or_senior_input_elt()
        #third_items.append(sub_or_senior_elt)
        third_items.append(widgets.HBox([widgets.Label(value='Seniority', layout={'width' : '150px'}), sub_or_senior_elt], layout={'padding' : '20px 0px '}))

        currency_elt = self._build_currency_elt()
        #third_items.append(currency_elt)        
        third_items.append(widgets.HBox([widgets.Label(value='Currency', layout={'width' : '150px'}), currency_elt], layout={'padding' : '20px 0px '}))   

        top_box = widgets.HBox(top_items)
        second_box = widgets.HBox(second_items)
        third_box = widgets.VBox(third_items, layout={'padding' : '30px'})

        #box = widgets.VBox([top_box,second_box, third_box], layout={'overflow_x':'hidden','overflow_y':'hidden'})
        box = widgets.HBox([widgets.VBox([top_box,second_box, third_box], layout={'overflow_x':'hidden','overflow_y':'hidden'}), ])
        # outer_box = widgets.HBox([box], layout={'overflow_x':'hidden','overflow_y':'hidden'})
        return box


    def __construct_top_level_table(self, df):
        #construct top level summary display
        ticker_display_str = self.app._strip_ticker(df.columns[0])

        outer_children=[]

        layout_label_dict = {'width':'200px','height':'19px','align_content':'flex-end'}
        layout_val_dict= {'width':'150px','height':'19px'}
        #Column Labels
        column_labels_children=[]
        id_col_label = widgets.HTML(value="<b>Ticker</b>",layout=layout_label_dict)
        val_col_label = widgets.HTML(value=ticker_display_str,layout=layout_val_dict)
        column_labels_children.append(id_col_label)
        column_labels_children.append(val_col_label)
        col_labels_box=widgets.HBox(column_labels_children, layout={'overflow_x':'hidden','overflow_y':'hidden'})

        outer_children.append(col_labels_box)

        for i in range(len(df.index)):
            ser = df.iloc[i]
            name = ser.name
            val = ser.iloc[0]
            if type(val) is float:
                val_str = "{:.1f}".format(val)
            else:
                val_str = str(val)
            name_label = widgets.HTML(value="<b>{}</b>".format(name),layout=layout_label_dict)
            val_label = widgets.HTML(value=val_str,layout=layout_val_dict)
            box = widgets.HBox([name_label,val_label], layout={'overflow_x':'hidden','overflow_y':'hidden'})
            outer_children.append(box)
            
        outer_box = widgets.VBox(outer_children)
        return outer_box        


    def __build_top_level_summary_area(self, df=None):

        if df is None:        
            ###Default if no data is available
            # tmp_button=widgets.Button(description='Placeholder for top level summary area', layout={'width':'500px'})
            # tmp_label =widgets.Label(value='Top Level Summary')
            # box = widgets.VBox([tmp_label,tmp_button])
            box = widgets.VBox([])
            return box

        #construct top_level_summary_display
        box_children = list()
        top_label =widgets.HTML(value='<b>Top Level Summary</b>')
        box_children.append(top_label)
        table_box = self.__construct_top_level_table(df)
        box_children.append(table_box)

        box = widgets.VBox(box_children)
        return box

    def _contruct_oas_ytw_data_table(self, df, digits_to_round=2):

        dfdg = df.round(digits_to_round).reset_index()

        dict_univ_labels = self.app.dict_data['univ_labels']

        default_col_width='160px'
        col_width_lookups = {'ID':'100px'}
        col_name_replacements = {'ID':'Maturity'}

        hbox = widgets.HBox()
        hbox_children = list()
        for col in dfdg.columns:
            #go through each column in dfdg
            #get headerName
            if col in col_name_replacements.keys():
                headerName = col_name_replacements[col]
            else:
                headerName = col
            #determine col_width
            if col in col_width_lookups.keys():
                col_width = col_width_lookups[col]
            else:
                col_width = default_col_width

            #construct vbox for column
            vbox = widgets.VBox(layout={'width':col_width,'overflow_x':'hidden'})
            vbox_children = list()

            #put in label for column header
            col_header_label = widgets.Button(description=str(headerName),layout={'width':'100%'},disabled=True)
            vbox_children.append(col_header_label)

            #go through all rows in the column
            for i in range(len(dfdg[col])):
                mat_label = dfdg['ID'].iloc[i]
                val = dfdg[col].iloc[i]
                button = widgets.Button(description=str(val),layout={'width':'100%'})

                if col in dict_univ_labels.keys():
                    univ_type=dict_univ_labels[col]
                else:
                    univ_type=""

                dict_button_info = {'col_name':col,'col_display_name':headerName,'maturity':mat_label,'univ_type':univ_type}
                self.dict_button_click_lookup[button]=dict_button_info
                button.on_click(self._clicked_OAS_YTW_button)

                if col=='ID':
                    button.disabled=True
                vbox_children.append(button)

            vbox.children = vbox_children
            hbox_children.append(vbox)

        hbox.children = hbox_children
        # hbox.layout.border='solid white 1px'

        return hbox

    def _clicked_OAS_YTW_button(self, button):
        button_info = self.dict_button_click_lookup[button]
        # self.update_status('Clicked button with info: {}'.format(button_info))
        univ_name = button_info['col_name']
        univ_type = button_info['univ_type']
        mat = button_info['maturity']
        # dict_univ_labels = self.app.dict_data['univ_labels']

        #navigate to drilldown tab
        self.output_area.selected_index = self.tab_names.index('Drilldown')

        ##populate settings to drilldown menus

        self.drilldown_ticker_element.value = self.app.dict_data['top_level_summary_data'].iloc[0].index[0]

        if mat =='All':
            mat_str = 'All Maturities'
        else:
            mat_str=mat
        self.drilldown_maturity_element.value=mat_str

        ##fill in univ_label
        if univ_type=='Ticker' or univ_type=='Ticker Only':
            self.drilldown_universe_element.value='Ticker Only'
        elif univ_type=='Sector':
            self.drilldown_universe_element.value='Sector'
        elif univ_type=='Rating':
            self.drilldown_universe_element.value='Rating Bucket'
        elif univ_type=='Industry Group':
            self.drilldown_universe_element.value='Industry Group'            
        elif univ_type=='Sector & Rating':
            self.drilldown_universe_element.value='Rating & Sector'
        elif univ_type=='Industry & Rating':
            self.drilldown_universe_element.value='Rating & Industry Group'            

        #trigger drilldown
        self._on_click_drilldown_button(value=None)

    def _contruct_oas_ytw_data_grid(self, df, digits_to_round=2):
        dfdg = df.round(digits_to_round).reset_index()
        col_defs=list()
        col_defs.append({'headerName':'Maturity','field':'ID','width':self.DEFAULT_DATAGRID_INDEX_WIDTH})

        for col_name in dfdg.columns[1:-2]:
            dc = {'headerName':col_name,'field':col_name,'width':self.DEFAULT_DATAGRID_COL_WIDTH}
            col_defs.append(dc)

        for col_name in dfdg.columns[-2:]:
            dc = {'headerName':col_name,'field':col_name,'width':self.DEFAULT_DG_COMBINED_COL_WIDTH}
            col_defs.append(dc)



    #     dg = bqwidgets.DataGrid(data=dfdg,column_defs=col_defs)
    #     dg.layout.width=self.DEFAULT_DATAGRID_WIDTH
    #     dg.layout.height = self.DEFAULT_DATAGRID_HEIGHT

    #     return dg



    def __construct_term_structure_display(self, label, df):
        box_children = list()
        label_obj = widgets.HTML(value="<b>{} Table</b>".format(label))
        box_children.append(label_obj)

        # dg = self._contruct_oas_ytw_data_grid(df)
        dg = self._contruct_oas_ytw_data_table(df)
        box_children.append(dg)


        ##build plot for term structure. One line for each column in DataFrame. 
        #The X-axis is the years to maturity. The Y-axis is the value of the metrics 
        #We need to translate from the term structure label (e.g. 3yr) to a number (e.g. 3)

        label_plot = widgets.HTML(value="<b>{} Term Structure</b>".format(label))
        box_children.append(label_plot)

        df2 = df.copy()
        try:
            df2.drop('All', inplace=True)
        except KeyError:
            pass
        s_interpolation_number = self.app.df_config_mat_buckets.set_index('label').loc[df2.index]['interpolation_number']

        df2.index=pd.Index(data=self.app.df_config_mat_buckets.set_index('label').loc[df2.index]['interpolation_number'].tolist(),name='ID')
        df2 = df2.loc[df2.index.dropna()]
        #don't display the "All" maturity column in the plot
        df2 = df2.iloc[~df2.index.isin(['All'])]

        self.dict_term_structure_plot_data[label]=df2

        # lineplot = bqv.LinePlot(df2).set_style()
        
        lineplot = px.line(df2)
        lineplot.update_layout(width=1000,
            plot_bgcolor= 'rgba(0, 0, 0, 0)',
            paper_bgcolor= 'rgba(0, 0, 0, 0)',
            yaxis = dict(color = 'white',title=""),
            xaxis = dict(color = 'white',title=""),
            legend = dict(bgcolor = 'rgba(0,0,0,0)',  ###set legend color, font, location
                          font=dict(color='white'),
                          title="",
                          yanchor='bottom',y=1.02,
                          # xanchor='right',x=1.4,
                          orientation='h')
        )
        lineplot.update_xaxes(showgrid=False,showline=True, linewidth=2, linecolor='white')   ### remove gridline at the background
        lineplot.update_yaxes(showgrid=False,showline=True, linewidth=2, linecolor='white',side='right')
#         lineplot.figure.legend_location = 'bottom-right'        
       
        plot_obj = go.FigureWidget(lineplot)
        
        box_children.append(plot_obj)


        return widgets.VBox(box_children,layout={'overflow_x':'hidden'})

    def __build_oas_ytw_display(self, d_oas_ytw):
        if d_oas_ytw is None:
            box = widgets.VBox([])
            return box
        hbox_children=list()
        outer_children=list()
        # top_label = widgets.Label(value='OAS & YTW by Maturity')        
        firstkey = next(iter(d_oas_ytw))
        df_term_structure = d_oas_ytw[firstkey]
        # df_ytw = d_oas_ytw['YTW']

        term_structure_display = self.__construct_term_structure_display(label='Average {}'.format(firstkey),df=df_term_structure)
        # ytw_display = self.__construct_term_structure_display(label='Average YTW',df=df_ytw)


        hbox_children.append(term_structure_display)
        # hbox_children.append(ytw_display)
        box = widgets.HBox(hbox_children)

        # outer_children.append(top_label)
        outer_children.append(box)
        outer_box = widgets.VBox(outer_children)
        return outer_box        

    def _build_fundamental_table_display(self, df):

        ##construct col_defs
        col_defs=list()
        col_defs.append({'headerName':'Ticker','field':'ID','width':self.DEFAULT_DATAGRID_INDEX_WIDTH_FUNDAMENTALS})

        for col_name in df.columns[0:]:
            dc = {'headerName':col_name,'field':col_name,'width':self.DEFAULT_DATAGRID_COL_WIDTH_FUNDAMENTALS}
            col_defs.append(dc)

        dfdg = df.round(2)

        self.fundamental_isdf = UtilityWidgets.InteractiveScatterDF(chart_title='Fundamentals on Peer Companies',default_x_axis='Debt To EBITDA', default_y_axis='EBITDA Margin',HIDDEN_OPACITY=0.2,column_for_size='Market Cap (B)', column_for_colors = 'Name')
        c = self.fundamental_isdf.create_bqp_dg_scatter(dfdg)
        l_selected = self.fundamental_isdf.datagrid.data[self.fundamental_isdf.datagrid.data.index==self.ticker_val].index.tolist()
        self.fundamental_isdf.datagrid.selected_row_indices=l_selected
        return c


        # dg = bqwidgets.DataGrid(data=dfdg.reset_index(),column_defs=col_defs)
        # dg.layout.width = self.DEFAULT_DATAGRID_WIDTH_FUNDAMENTALS
        # dg.layout.height = self.DEFAULT_DATAGRID_HEIGHT_FUNDAMENTALS
        # return dg

    def __build_fundamental_display(self, df, description=None):
        if df is None:
            box = widgets.VBox([])
            return box

        vbox_children = list()
        if description is None:
            label = widgets.HTML(value='<b>Fundamentals on Peer Companies</b>')
        else:
            label = widgets.HTML(value='<b>{}</b>'.format(description))
        dg = self._build_fundamental_table_display(df)

        vbox_children.append(label)
        vbox_children.append(dg)
        vbox = widgets.VBox(vbox_children, layout={'overflow_x':'hidden'})

        return vbox

    def __on_change_dropdown_selection(self,value):
        if value['name']=='value' and value['new']!='--choose maturity bucket--':            
            self.app.log_message("Selected to calculate trends for {} for {}".format(value['new'],self.ticker_val),spinner=True)
            mat_bucket_str=value['new']
            ticker= self.ticker_val
            old_children = list(self.trends_area.children)
            #make spinner box visible
            old_children = self.trends_area.children
            new_children = list(old_children)
            new_children.append(self.spinner_box)

            seniority_str=None
            if self.sub_or_senior_radio.value=='Sub':
                seniority_str='Sub'
            elif self.sub_or_senior_radio.value=='Senior':
                seniority_str='Senior'

            metric_str = None
            # if self.metric_chooser_elt.value=='OAS':
            #     metric_str = 'OAS'
            # elif self.metric_chooser_elt.value=='YTW':
            #     metric_str = 'YTW'
            metric_str = self.metric_chooser_elt.value

            ccy_str = self._get_ccy_str()


            self.trends_area.children = new_children            
            #get trend data
            self.trend_data = self.app._get_trend_data(mat_bucket_str=mat_bucket_str, ticker=ticker, seniority_str=seniority_str, metric_str=metric_str, ccy_str=ccy_str)
            
            #get rid of spinner box
            self.trends_area.children = old_children
            
            self._build_trends_chart(self.trend_data)

            self.app.log_message("Done getting trend data for {}".format(self.ticker_val),spinner=False)

    def _build_trends_chart(self, trend_data):

        new_children = list()

        # new_children.append(widgets.Label('Need to build a chart for maturity bucket {} and ticker {}'.format(mat_bucket_str, ticker)))
        # self.trend_data = self.app._get_trend_data(mat_bucket_str=mat_bucket_str, ticker=ticker)
        if trend_data is None:
            self.trend_chart_area.children=new_children
            return 

        #build charts with self.trend_data
        plots=list()
        for metric_name in trend_data.keys():
            df = trend_data[metric_name]
            label = widgets.HTML("<b>{}</b>".format(metric_name))
           
            # lineplot = bqv.LinePlot(df).set_style()
            
            
            lineplot = px.line(df)
            lineplot.update_layout(width=1000,
                plot_bgcolor= 'rgba(0, 0, 0, 0)',
                    paper_bgcolor= 'rgba(0, 0, 0, 0)',
                    yaxis = dict(color = 'white',title=""),
                    xaxis = dict(color = 'white',title=""),
                    legend = dict(bgcolor = 'rgba(0,0,0,0)',  ###set legend color, font, location
                                  font=dict(color='white'),
                                  title="",
                                  yanchor='bottom',y=1.02,
                                  # xanchor='right',x=1.4,
                                  orientation='h')
            )
            lineplot.update_xaxes(showgrid=False,showline=True, linewidth=2, linecolor='white')   ### remove gridline at the background
            lineplot.update_yaxes(showgrid=False,showline=True, linewidth=2, linecolor='white',side='right')
        
            plot_obj = go.FigureWidget(lineplot)
            
            ##datagrid for data transparency
            dfdg = df.round(2)
            
            dfdg.index = dfdg.index.strftime('%Y-%m-%d')
            dfdg.index.name='Date'
            dg = ipydatagrid.DataGrid(dfdg, 
                                      base_column_size=self.DEFAULT_DATAGRID_COL_WIDTH,
                                      column_widths={'Date': self.DEFAULT_DATAGRID_INDEX_WIDTH})
            dg.layout.width=self.DEFAULT_DATAGRID_WIDTH_TREND
            dg.layout.height = self.DEFAULT_DATAGRID_HEIGHT_TREND
            
            box = widgets.VBox([label,plot_obj,dg])
            plots.append(box)

        hbox = widgets.HBox(plots)
        new_children.append(hbox)

        self.trend_chart_area.children=new_children

    def _build_settings_area(self):
        return widgets.VBox([self._build_settings_display()])

    def _build_trends_area(self):

        vbox_children = list()
        label = widgets.HTML(value='<b>Trend by Maturity Bucket</b>')
        vbox_children.append(label)

        #construct Dropdown
        l_mat_options = list()
        l_mat_options.append('--choose maturity bucket--')
        l_mat_options.extend(self.app.df_config_mat_buckets['label'].tolist())
        l_mat_options.append('All Maturities')
        dropdown = widgets.Dropdown(options = l_mat_options, value='--choose maturity bucket--')
        dropdown.observe(self.__on_change_dropdown_selection)
        vbox_children.append(dropdown)

        ##construct trend chart
        self.trend_chart_area = widgets.VBox([],layout={'overflow_x':'hidden'})
        vbox_children.append(self.trend_chart_area)

        vbox = widgets.VBox(vbox_children)
        return vbox

    def __build_metric_chooser_elt(self):
        l_metrics = self.app.get_list_of_metric_names()
        self.metric_chooser_elt = widgets.Dropdown(description='Metric',options=l_metrics,value=l_metrics[0])
        return self.metric_chooser_elt


    def __build_universe_filtering_elt(self):
        style = {'description_width': 'initial'}
        #self.univ_radio = widgets.RadioButtons(options=['Index','Entire Bonds'],description='Comparison Universe', style=style,layout={'max_width':'240px'})
        self.univ_radio = widgets.RadioButtons(options=['Index','Entire Bonds'],description='', style=style,layout={'max_width':'120px'})
        self.univ_radio.observe(self.__on_change_univ_radio)
        self.index_univ_box_area = widgets.VBox([], layout={'overflow_x':'hidden','overflow_y':'hidden'})
        # self.index_univ_text_elt = widgets.Text(value='LUACTRUU Index',layout={'width':'150px'})
        self.index_univ_text_elt = bqwidgets.TickerAutoComplete(value=self.DEFAULT_INDEX_STRING, yellow_keys=['Index'], layout={'width':'150px'})
        self.index_univ_box_area.children=[self.index_univ_text_elt]
        #box = widgets.HBox([self.univ_radio, self.index_univ_box_area], layout={'overflow_x':'hidden', 'overflow_y':'hidden'})
        box = widgets.HBox([widgets.Label(value='Comparison Universe', layout= {'width' : '150px'}), self.univ_radio, self.index_univ_box_area], layout={'overflow_x':'hidden', 'overflow_y':'hidden'})
        return box

    def __on_change_univ_radio(self, value):
        if value['name'] != 'value':
            return
        if value['new']=='Index':
            ##selected Index
            self.index_univ_box_area.children=[self.index_univ_text_elt]
        else:
            self.index_univ_box_area.children=[]
            #selected away from index

    def _build_ticker_input_elt(self):
        # self.ticker_input = widgets.Text(value='',description='Ticker',disabled=False)
        self.ticker_input = bqwidgets.TickerAutoComplete(description='Company',value='BA US Equity',yellow_keys=['Equity'],disabled=False,button_style='success',tooltip='Click to Analyze Company')
        self.ticker_submit_button = widgets.Button(description='Analyze',disabled=False,button_style='success',tooltip='Click to Analyze Company')
        self.ticker_submit_button.on_click(self._on_click_analyze_button)
        box = widgets.HBox([self.ticker_input, self.ticker_submit_button], layout={'overflow_x':'hidden','overflow_y':'hidden'})
        return box

    def _build_sub_or_senior_input_elt(self):
        #self.sub_or_senior_radio = widgets.RadioButtons(options=['All','Sub','Senior'], description='Seniority',style={'description_width': 'initial'})
        self.sub_or_senior_radio = widgets.RadioButtons(options=['All','Sub','Senior'],style={'description_width': 'initial'})
        return self.sub_or_senior_radio

    def _build_currency_elt(self):
        #self.currency_radio=widgets.RadioButtons(description='Currency',options=['All','Single'],value='Single',disabled=False,layout={'max_width':'240px'})
        self.currency_radio=widgets.RadioButtons(description='',options=['All','Single'],value='Single',disabled=False,layout={'max_width':'120px'})
        self.currency_text_input = widgets.Dropdown(value='USD',options=['USD','EUR','JPY','CAD','GBP','AUD'], layout ={'width': '150px'})
        self.currency_input_area = widgets.HBox([self.currency_radio, self.currency_text_input])
        self.currency_radio.observe(self._changed_currency_radio)
        return self.currency_input_area

    def _changed_currency_radio(self,value):
        if value['name'] != 'value':
            return
        if value['new']=='All':
            ##selected Index
            self.currency_input_area.children=[self.currency_radio]
        else:
            self.currency_input_area.children=[self.currency_radio,self.currency_text_input]


        
    def __build_output_area(self):
        tab_children = list()
        self.tab_names = list()

        tab_children.append(self.input_area)
        self.tab_names.append('Input Parameters')

        tab_children.append(self.top_level_summary_area)
        self.tab_names.append('Top Level Summary')

        # self.output_area_children=[]        
        self.term_structure_area = widgets.HBox([])        
        tab_children.append(self.term_structure_area)
        self.tab_names.append('Term Structure')

        # tmp=widgets.Textarea(value='Placeholder for OAS YTW')
        self.term_structure_area.children=[]        
        # self.output_area_children.append(self.term_structure_area)

        self.trends_area = widgets.VBox([])
        tab_children.append(self.trends_area)
        self.tab_names.append('Trend')

        # self.output_area_children.append(self.trends_area)


        # self.drilldown_area = widgets.HBox([])
        # self.output_area_children.append(self.drilldown_area)

        self.fundamental_area = widgets.VBox([])
        tab_children.append(self.fundamental_area)
        self.tab_names.append('Fundamentals')

        self.drilldown_area = widgets.VBox([self.__build_drilldown_display()])
        tab_children.append(self.drilldown_area)
        self.tab_names.append('Drilldown')

#         self.settings_area = widgets.VBox([self._build_settings_display()])
#         tab_children.append(self.settings_area)        
#         self.tab_names.append('settings')

        # self.output_area_children.append(self.fundamental_area)

        tab = widgets.Tab()
        tab.children = tab_children
        for i in range(len(tab_children)):
            tab.set_title(i, self.tab_names[i])
        return tab

    def _build_settings_display(self):
        box = widgets.VBox([])
        bql_refresh_button=widgets.Button(description='Refresh BQL Connection',layout={'width':'250px'})
        bql_refresh_button.on_click(self._clicked_bql_refresh_button)
        box.children=[bql_refresh_button]
        return box


    def __build_drilldown_display(self):
        box = widgets.VBox([])
        self.drilldown_output_box=widgets.VBox([])

        input_children=list()


        ##ticker element
        # self.drilldown_ticker_element = bqwidgets.TickerAutoComplete(description='Ticker',value='', yellow_keys=['Equity'])
        self.drilldown_ticker_element = widgets.Text(description='Ticker',value='')
        input_children.append(self.drilldown_ticker_element)        

        #universe element
        universes=['Ticker Only', 'Rating Bucket', 'Sector','Industry Group', 'Rating & Sector', 'Rating & Industry Group']
        self.drilldown_universe_element = widgets.Dropdown(description='Universe',options=universes)
        input_children.append(self.drilldown_universe_element)


        ##maturity element
        l_mats= []
        try:
            l_mats.extend(self.app.df_config_mat_buckets['label'].tolist().copy())
        except:
            pass
        l_mats.append('All Maturities')
        self.drilldown_maturity_element = widgets.Dropdown(description='Maturity',options=l_mats)
        input_children.append(self.drilldown_maturity_element)
        try:
            self.drilldown_maturity_element.value='5yr'
        except:
            pass

        ##max_num_results element
        self.drilldown_max_num_results_element = widgets.IntText(value=100,max=500,description='Max Results')
        input_children.append(self.drilldown_max_num_results_element)


        ##submit button
        drilldown_submit_button = widgets.Button(description='Compute Drilldown', button_style='success')
        drilldown_submit_button.on_click(self._on_click_drilldown_button)
        # input_children.append(drilldown_submit_button)


        drilldown_input_selection_box = widgets.VBox(input_children)
        self.drilldown_input_box= widgets.HBox([drilldown_input_selection_box,drilldown_submit_button])
        box.children=[self.drilldown_input_box,self.drilldown_output_box]


        return box

    def _on_click_drilldown_button(self, value):
        # self.update_status('Computing drilldown on ticker "{}", Maturity "{}", Universe "{}"'.format(self.drilldown_ticker_element.value, self.drilldown_maturity_element.value, self.drilldown_universe_element.value),spinner=True)

        univ_selector_str = self.univ_radio.value
        index_str = self.index_univ_text_elt.value
        seniority_str = self.sub_or_senior_radio.value
        ccy_str = self._get_ccy_str()        


        max_num_results=self.drilldown_max_num_results_element.value

        self.app.compute_drilldown(ticker=self.drilldown_ticker_element.value, 
            mat_str=self.drilldown_maturity_element.value, 
            univ_str=self.drilldown_universe_element.value,
            univ_selector_str=univ_selector_str,
            index_str=index_str,
            seniority_str=seniority_str,
            ccy_str = ccy_str,            
            max_num_results=max_num_results)

        if 'drilldown' in self.app.dict_data.keys():
            data = self.app.dict_data['drilldown']
            self._render_drilldown_bqplot(data)

    def _clicked_bql_refresh_button(self, value):
        self.update_status('Refreshing BQL Connection...',spinner=True)
        self.app.bql_util._refresh_bql_service()
        self.update_status('Completed refreshing BQL Connection.',spinner=False)        
        
    def _construct_spinner(self):
        #item = widgets.HTML('<img src="/files/ajax-loader_1.gif">')        
        #out = widgets.Output(layout={'border': '0px solid black', 'width':'40px','height':'40px'})
        #with out:
        #    display(item)
        #return out        
        item = widgets.Image.from_file('ajax-loader_1.gif', layout={'width':'20px', 'height':'20px'})
        #item = widgets.Image.from_file('ajax-loader_1.gif', width=20, height=20)
        return item

    def _on_click_analyze_button(self, button):
        # print('clicked analyze button, with value {}'.format(button))
        self.ticker_val = self.ticker_input.value

        if len(self.ticker_val)==0:
            self.update_status('You must enter an equity ticker to analyze',color='yellow')
            return

        self.update_status('Clicked Analyze Button for ticker: {}'.format(self.ticker_val),spinner=True)
        if self.univ_radio.value=='Index':
            start_univ_override_str = self.index_univ_text_elt.value
        else:
            start_univ_override_str = None

        seniority_str=None
        if self.sub_or_senior_radio.value=='Sub':
            seniority_str='Sub'
        elif self.sub_or_senior_radio.value=='Senior':
            seniority_str='Senior'

        # metric_str = None
        # if self.metric_chooser_elt.value=='OAS':
        #     metric_str = 'OAS'
        # elif self.metric_chooser_elt.value=='YTW':
        #     metric_str = 'YTW'
        metric_str = self.metric_chooser_elt.value

        ccy_str = self._get_ccy_str()

        try:
            self.output_area.selected_index = self.tab_names.index('Top Level Summary')            
            self.app.do_analyze(ticker=self.ticker_val, start_univ_override_str=start_univ_override_str, seniority_str=seniority_str, metric_str=metric_str,ccy_str=ccy_str)

        except RuntimeError as rte:
            self.update_status('Unknown Exception running Analysis: {}'.format('<br>'.join(traceback.format_exc().splitlines())),color='Yellow')
        except Exception as exc:
            self.update_status('Unknown Exception running Analysis: {}'.format('<br>'.join(traceback.format_exc().splitlines())),color='Yellow')
            self.temp_err = exc

        # self.redraw_gui()

    def construct_display_messages_for_drilldown(self, dict_drilldown):
        display_messages=list()
        if dict_drilldown['univ_str']=='Ticker Only':
            display_messages.append("Drilldown on Ticker: {}".format(dict_drilldown['ticker']))
            # top_item=widgets.HTML(value="Drilldown on Ticker: {}".format(dict_drilldown['ticker']),layout=layout_dict)
            # children.append(top_item)
        elif dict_drilldown['univ_selector_str']=='Index':
            display_messages.append("Drilldown to {}".format(dict_drilldown['index_str']))
            # top_item=widgets.HTML(value="Drilling down to {}".format(dict_drilldown['index_str']),layout=layout_dict)
            # children.append(top_item)
        elif dict_drilldown['univ_selector_str']=='Entire Bonds':
            display_messages.append("Drilldown to full bonds universe")
            # top_item=widgets.HTML(value="Drilling down to full bonds universe",layout=layout_dict)
            # children.append(top_item)
            
        if dict_drilldown['univ_str']=='Rating Bucket':
            display_messages.append("Rating: {}".format(dict_drilldown['rating_bucket']))
            # top_item =widgets.HTML(value="Drilldown on Rating Bucket: {}".format(dict_drilldown['rating_bucket']),layout=layout_dict)
            # children.append(top_item)
        elif dict_drilldown['univ_str']=='Sector':
            display_messages.append("Sector: {}".format(dict_drilldown['sector']))
            # top_item =widgets.HTML(value="Drilldown on Sector: {}".format(dict_drilldown['sector']),layout=layout_dict)
            # children.append(top_item)    
        elif dict_drilldown['univ_str']=='Industry Group':
            display_messages.append("Industry Group: {}".format(dict_drilldown['industry_group']))
            # top_item =widgets.HTML(value="Drilldown on Industry Group: {}".format(dict_drilldown['industry_group']),layout=layout_dict)
            # children.append(top_item)        
        elif dict_drilldown['univ_str']=='Rating & Sector':
            display_messages.append("Rating & Sector: {} & {}".format(dict_drilldown['rating_bucket'],dict_drilldown['sector']))
            # top_item =widgets.HTML(value="Drilldown on Rating: {} & Sector: {}".format(dict_drilldown['rating_bucket'],dict_drilldown['sector']),layout=layout_dict)
            # children.append(top_item)        
        elif dict_drilldown['univ_str']=='Rating & Industry Group':    
            display_messages.append("Rating & Industry Group: {} & {}".format(dict_drilldown['rating_bucket'],dict_drilldown['industry_group']))
            # top_item =widgets.HTML(value="Drilldown on Rating: {} & Industry Group: {}".format(dict_drilldown['rating_bucket'],dict_drilldown['industry_group']),layout=layout_dict)
            # children.append(top_item)           
            
        if dict_drilldown['mat_str']=='All Maturities':
            # item = widgets.HTML(value='All Maturities',layout=layout_dict)
            display_messages.append("All Maturities")
        else:
            display_messages.append('Maturity bucket: {}'.format(dict_drilldown['mat_str']))   
        return display_messages     


    def __construct_drilldown_summary_description_item(self, dict_drilldown):
        # display_messages=list()
        children = list()
        layout_dict={'height':'20px','align_items':'flex-end','display':'flex'}
        display_messages = self.construct_display_messages_for_drilldown(dict_drilldown)
            # item = widgets.HTML(value='Maturity bucket: {}'.format(dict_drilldown['mat_str']),layout=layout_dict)
        # children.append(item)
        item = widgets.HTML(value="; ".join(display_messages),layout=layout_dict)
        children.append(item)

        box = widgets.VBox(children, layout={'overflow_x':'hidden', 'overflow_y':'hidden'})
        return box

    def _construct_drilldown_plot(self, df_drilldown):

        remove_cols = ['Currency','Coupon Type','Payment Rank']
        ##remove some columns
        for col in remove_cols:
            if col in df_drilldown.columns:
                df_drilldown = df_drilldown.drop(col,axis=1)
                
        fig_params=dict(height=400,width=600 , margin=dict(l=60, r=30, t=70, b=40))
        self.drilldown_iscat=sc.GOInteractiveScatterPlot(df_drilldown,**fig_params)

#         self.drilldown_iscat = bqv.InteractiveScatterPlot(df_drilldown.drop(['Name','Ticker'],axis=1), reg_line=False)
#         self.drilldown_iscat.x='Years to mat'
#         self.drilldown_iscat.y='OAS'
#         self.drilldown_iscat.figure.layout.min_width='600px'
#         self.drilldown_iscat.figure.layout.min_height='500px'

        return go.FigureWidget(self.drilldown_iscat)      

    def _update_drilldown_datagrid_data(self, df):
        self.drilldown_dg.data = df.sort_values('Amt Out (M)',ascending=False).reset_index().round(2)

    def _construct_dg_col_defs(self, df):
        l_metric_names = self.app.get_list_of_metric_names()
        col_defs = list()        
        for col_name in df.columns:
            if col_name=='ID':
                col_defs.append({'headerName':'ID','field':col_name,'width':self.DEFAULT_DATAGRID_COL_WIDTH})
            elif col_name=='Ticker':
                col_defs.append({'headerName':'Eq Tkr','field':col_name,'width':75})
            elif col_name=='Years to mat':
                col_defs.append({'headerName':'Yrs to mat','field':col_name,'width':100})

            elif col_name in l_metric_names:
                col_defs.append({'headerName':col_name,'field':col_name,'width':100})                
            else:
                col_defs.append({'headerName':col_name,'field':col_name,'width':self.DEFAULT_DATAGRID_COL_WIDTH})
        return col_defs



    def __construct_drilldown_datagrid(self, df_drilldown):
        df = df_drilldown.sort_values('Amt Out (M)',ascending=False).reset_index()
        #constuct column defs
#         col_defs=self._construct_dg_col_defs(df)

#         dg = bqwidgets.DataGrid(data=df.round(2),column_defs=col_defs)
        l_metric_names = self.app.get_list_of_metric_names()
        column_widths = dict(zip(l_metric_names, [100]*len(l_metric_names)))
        column_widths['Eq Tkr'] = 75
        column_widths['Yrs to mat'] = 100
        dg = ipydatagrid.DataGrid(df.round(2), 
                                  base_column_size=self.DEFAULT_DATAGRID_COL_WIDTH,
                                  column_widths=column_widths)
        dg.layout.min_width='750px'
        dg.layout.height='500px'        
        return dg

    def _on_click_drilldown_filtering(self, value):
        selected_data = self.drilldown_iscat.selected_data
        if selected_data is not None:
            self.update_status('Clicked drilldown filtering button with {} points selected'.format(len(selected_data)))

        ##filter the display of datagrid to match points selected in scatter plot
        df_orig = self.app.dict_data['drilldown']['df']

        if selected_data is None or len(selected_data)==0:
            self._update_drilldown_datagrid_data(df_orig)
        else:
            self._update_drilldown_datagrid_data(df_orig.loc[selected_data.index])

        # self.drilldown_dg.data=selected_data

    def _on_click_drilldown_reset(self, value):
        df_orig = self.app.dict_data['drilldown']['df']
        self._update_drilldown_datagrid_data(df_orig)  
        self.drilldown_iscat.selected_data=None

    def _render_drilldown_bqplot(self, data):
        # self.update_status('Need to render drilldown data......')
        dict_drilldown = self.app.dict_data['drilldown']
        summary_item = self.__construct_drilldown_summary_description_item(dict_drilldown)
        self.df_drilldown = dict_drilldown['df']
        
        l_display_messages = self.construct_display_messages_for_drilldown(dict_drilldown)
        chart_title = "; ".join(l_display_messages)
        self.isdf = UtilityWidgets.InteractiveScatterDF(chart_title=chart_title, default_x_axis='Years to mat', default_y_axis='OAS', column_for_size='Amt Out (M)')
        self.drilldown_display = self.isdf.create_bqp_dg_scatter(self.df_drilldown)
        self.drilldown_output_box.children=[summary_item, self.drilldown_display]        



    def _render_drilldown_bqviz(self, data):
        # self.update_status('Need to render drilldown data......')
        ##OLD
        dict_drilldown = self.app.dict_data['drilldown']
        summary_item = self.__construct_drilldown_summary_description_item(dict_drilldown)
        self.df_drilldown = dict_drilldown['df']
        chart_label = dict_drilldown['index_str']

        self.drilldown_dg = self.__construct_drilldown_datagrid(self.df_drilldown)
        drilldown_plot = self._construct_drilldown_plot(self.df_drilldown)
        drilldown_filtering_button = widgets.Button(description='Filter on Selection', button_style='info')
        drilldown_reset_button = widgets.Button(description='Reset Filtering',button_style='warning')
        drilldown_filtering_button.on_click(self._on_click_drilldown_filtering)
        drilldown_reset_button.on_click(self._on_click_drilldown_reset)
        drilldown_plot_area = widgets.VBox([drilldown_plot, drilldown_filtering_button, drilldown_reset_button])
        box_dg_and_plot = widgets.HBox([self.drilldown_dg,drilldown_plot_area])
        self.drilldown_output_box.children=[summary_item, box_dg_and_plot]



    def redraw_gui(self, l_str_section=None, force_clear=False):
        dict_data = self.app.dict_data

        if l_str_section is None:            
            ##draw all sections
            l_str_section = ['top_level_summary','term_structure','fundamental','trends','drilldown','settings']

        if force_clear:
            top_level_summary_box = self.__build_top_level_summary_area(df=None)
            self.top_level_summary_area.children = [top_level_summary_box]

            oas_ytw_display = self.__build_oas_ytw_display(d_oas_ytw=None)
            self.term_structure_area.children=[oas_ytw_display]

            fundamental_box = self.__build_fundamental_display(df=None)
            self.fundamental_area.children=[fundamental_box]

            trends_box = widgets.VBox([])
            self.trends_area.children=[trends_box]          

            drilldown_box = self.__build_drilldown_display()
            self.drilldown_area.children=[drilldown_box]

#             settings_box = widgets.VBox([])  
#             self.settings_area.children=[settings_box]

        for section in l_str_section:

            if section=='top_level_summary' and 'top_level_summary_data' in dict_data.keys():
                df_top_level = dict_data['top_level_summary_data']
                top_level_summary_box = self.__build_top_level_summary_area(df=df_top_level)
                self.top_level_summary_area.children = [top_level_summary_box]

            if section=='term_structure' and 'oas_ytw_data' in dict_data.keys():
                d_oas_ytw = dict_data['oas_ytw_data']
                oas_ytw_display = self.__build_oas_ytw_display(d_oas_ytw=d_oas_ytw)
                self.term_structure_area.children=[oas_ytw_display]


            if section=='fundamental' and 'fundamental_data' in dict_data.keys():
                fundamental_data = dict_data['fundamental_data']
                df_fundamental_data = fundamental_data['df']
                fundamental_data_description = fundamental_data['description']
                fundamental_box = self.__build_fundamental_display(df_fundamental_data, description=fundamental_data_description)
                self.fundamental_area.children=[fundamental_box]

            if section=='trends':
                trends_box = self._build_trends_area()
                self.trends_area.children=[trends_box]

            if section=='drilldown':
                drilldown_box = self.__build_drilldown_display()
                self.drilldown_area.children=[drilldown_box]                

#             if section=='settings':
#                 settings_box = self._build_settings_area()
#                 self.settings_area.children=[settings_box]

    def _get_ccy_str(self):
        ccy_str = None
        if self.currency_radio.value=='Single':
            ccy_str = self.currency_text_input.value              
        return ccy_str

    def update_status(self, msg, color=None, spinner=False, preserve_spinner=False):
        """
        Utility to display custom status messages to UI
        """
        if preserve_spinner:
            spinner = self.is_spinner_on

        if spinner:
            self.spinner_box.children = [self._construct_spinner()]
            self.is_spinner_on=True
        else:
            self.spinner_box.children = []
            self.is_spinner_on=False
        self.app_logger.log_message(msg, color=color)        
        
    def show(self):
        return self.canvas
        