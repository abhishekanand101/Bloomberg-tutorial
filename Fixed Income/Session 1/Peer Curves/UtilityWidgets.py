from collections import deque
import datetime as dt
from IPython.display import display
from ipywidgets import HTML


import bqplot as bqp
import pandas as pd
import numpy as np
import ipywidgets as widgets
import ipydatagrid
import bqwidgets 

class ApplicationLogger(object):
    """
    Summary:
        GUI for an HTML widget that can provide
        information to the user through what
        is effectively a console window.
    """
    def __init__(self, max_msgs=20, layout_dict=None):
        # create a dictionary to store each widget we build
        self.widgets = dict()
        
        # create a message queue for storing
        # messages with a max length that is
        # provided by the user
        self.msg_queue = deque(maxlen=max_msgs)
        
        # we need to check and validate our layout_dict
        # to make sure it is not None
        validated_layout_dict = self.__validate_layout_dict(layout_dict)

        # construct the HTML widget we will be
        # using to display messages
        self.__create_html_widget(validated_layout_dict)
    
    def __validate_layout_dict(self, layout_dict):
        """
        Summary:
            Checks the layout_dict provided when the object
            is instantiated to see if it is None. If it is
            None then we utilize the default CSS layout
            dictionary in this class.
        
        Args:
            - layout_dict (dict or None): CSS property dictionary provided at
                                          object instantiation
        
        Returns:
            - validated_layout_dict (dict): CSS property dictionary for widget
        """
        if layout_dict is None:
            validated_layout_dict = self.__get_default_layout_dict()
        else:
            validated_layout_dict = layout_dict

        return validated_layout_dict

    def __get_default_layout_dict(self):
        """
        Summary:
            This funcion is called if the user
            does not provide anything to the
            'layout_dict' arg when instantiating
            this class. This is the default
            layout parameters to be used in the widget
        
        Returns:
            - default_layout (dict): dictionary containing default
                                     CSS layout parameters
        """
        default_layout = {'display' : 'flex',
                          'max_height' : '75px',
                          'overflow_y' : 'auto',
                          'border' : '2px solid white'}
        return default_layout

    def log_message(self, msg, color=None):
        """
        Summary:
            This function is called by an external application
            which wants this HTML widget to display some
            message to the user.
        
        Args:
            - msg (string): Message to display in HTML console
            - color (optional, string): HTML color of the text
        """
        # add color to our message
        if color is not None:
            msg_color_temp = """<font color="{font_color}">{user_msg}</font>"""
            msg = msg_color_temp.format(font_color=str(color),
                                        user_msg=msg)
        # get the current timestamp as a string
        timestamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # combine the timestamp with the message
        modified_msg = "%s - %s" % (timestamp, msg)
        
        # store the enriched message in our message queue
        self.msg_queue.appendleft(modified_msg)
        
        # update the HTML console with the latest message
        self.__update_html_console()

    def __create_html_widget(self, validated_layout_dict):
        """
        Summary:
            Creates the HTML widget which will be used
            to display our messages and store it in
            the self.widgets dictionary

        Args:
            - validated_layout_dict (dict): dictionary containing CSS
                                            properties for widget layout
        """
        widget_html_console = HTML('', layout=validated_layout_dict)
        self.widgets['html_console'] = widget_html_console
    
    def __update_html_console(self):
        """
        Summary:
            Updates the HTML widget console with the
            latest set of messages
        """
        # concatenate the message strings into HTML format
        html_string = "<br>".join(list(self.msg_queue))
        # update the 'value' of the HTML widget to display
        # the latest messages to the user
        self.widgets['html_console'].value = html_string
    
    def get_widget(self):
        """
        Summary:
            This function is called by an external application
            to obtain the underlying widget for when we
            display the external application to the user.
        
        Returns:
            - widget_html_console (ipywidgets.HTML): HTML widget with our displayed messages
        """
        widget_html_console = self.widgets['html_console']
        return widget_html_console
    
    def display_widget(self):
        """
        Summary:
            This function forces Jupyter Notebook to display
            our widget. This should not be used in most instances
            since this widget is part of a larger application.
        """
        display(self.widgets['html_console'])
        
        
class InteractiveScatterDF(object):
    def __init__(self, default_x_axis=None, default_y_axis=None, chart_title=None, l_metric_names=None, DEFAULT_DG_HEIGHT='500px',DEFAULT_DG_WIDTH='600px', HIDDEN_OPACITY=0.1, column_for_size='Amt Out (M)', column_for_colors='Ticker'):
        if chart_title is None:
            chart_title='Chart'        
        self.chart_title=chart_title
        
        if l_metric_names is None:
            self.l_metric_names=None
        else:
            self.l_metric_names=tuple(l_metric_names)
            
        self.dg_col_defs = {'Name': 160,
                            'ID':120,
                            'Eq Tkr': 75,
                            'OAS': 100,
                            'YTW': 100,
                            'Z Spread': 100,
                            'Yrs to mat': 100,
                            'Amt Out (M)': 140,
                            'Currency': 140,
                            'Coupon Type': 140,
                            'Payment Rank': 140,
                            'Ticker': 150,
                            'Market Cap (B)': 160,
                            'Debt To EBITDA': 160,
                            'Sales (B)': 160,
                            'EBITDA (B)': 160,
                            'EBITDA Margin': 160,
                            'Free Cash Flow (B)': 160}
        
        self.DEFAULT_DG_HEIGHT = DEFAULT_DG_HEIGHT
        self.DEFAULT_DG_WIDTH = DEFAULT_DG_WIDTH
        
        self.default_x_axis = default_x_axis
        self.default_y_axis = default_y_axis
        self.hidden_opacity = HIDDEN_OPACITY
        self.column_for_size = column_for_size
        self.column_for_colors = column_for_colors
        
    # Define callback function for dropdown widgets
    def update_plot(self, evt):
        if evt is not None:
            ###need to determine what the new dataframe is
            x_val = self.dropdown_x.value
            y_val = self.dropdown_y.value
            if x_val == y_val:
                df_new_raw = self.dataframe[[x_val]]
                df_new = df_new_raw.dropna()
                # self.df_scatter = df_new
            else:
                df_new_raw = self.dataframe[[x_val,y_val]]
                df_new = df_new_raw.dropna()
                # self.df_scatter = df_new

            self.df_scatter = self.dataframe.loc[df_new.index]
            self.mark_scatter.x = df_new[x_val]
            self.axis_x.label = x_val
            self.mark_scatter.y = df_new[y_val]
            self.axis_y.label = y_val
            
            

    # Define callback function for selections
    def on_select_scatter(self,evt):
        # print(evt)
        if evt is not None and evt['new'] is not None:
            indices = evt['new']
            if len(indices) == 0:
                self.datagrid.data = self.df_scatter.round(2)
                self.reset_opacities()                
            else:
                self.datagrid.data = self.df_scatter.iloc[indices].round(2)
                self.datagrid.selected_row_indices=list(range(len(self.datagrid.data)))
                
        #update opacities
        l_ids = self.datagrid.data.index.tolist()
        df_orig = self.df_scatter.reset_index()
        original_indices = df_orig[df_orig['ID'].isin(l_ids)].index.tolist()

        if len(original_indices)==0:
            self.reset_opacities()
            return
        l_opacities = list(range(len(self.mark_scatter.x)))
        l_opacities = [self.translate_opacity(x, original_indices) for x in l_opacities]
        self.mark_scatter.default_opacities=l_opacities

        

    def translate_opacity(self,i,l):
        if i in l:
            return 1.0
        else:
            return self.hidden_opacity                

    def reset_opacities(self):
        self.mark_scatter.default_opacities=[1]
    
    def on_click_dg(self, val):
        
        l_d_sel = self.datagrid.selected_cells
        selected_indices = list(set([x['r'] for x in l_d_sel]))
        
        df_dg = self.datagrid.get_visible_data().iloc[selected_indices]

        df_orig = self.df_scatter.reset_index()
        original_indices = df_orig[df_orig['ID'].isin(df_dg.reset_index().ID)].index.tolist()        


        if len(selected_indices)==0:
            self.reset_opacities()
            return

        visible_data = self.datagrid.get_visible_data()
        df_selected = visible_data.iloc[selected_indices]


        l_opacities = list(range(len(self.mark_scatter.x)))
        l_opacities = [self.translate_opacity(x, original_indices) for x in l_opacities]
        # print(l_opacities)
        self.mark_scatter.default_opacities=l_opacities

    def create_colors_list(self, df):
        l_color_master_list = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', 
                               '#bcbd22', '#17becf', '#FF6347','#FFD700','#FFFF00','#00FA9A','#006400','#00FFFF','#7B68EE','#FF00FF']

        #construct mapping from ticker to color
        l_unique_tickers = df.sort_values(self.column_for_size,ascending=False)[self.column_for_colors].unique()
        d_ticker_to_color = dict()
        pointer = 0
        for i in range(len(l_unique_tickers)):
            if pointer >= len(l_color_master_list):
                pointer = pointer -len(l_color_master_list)
            newcolor = l_color_master_list[pointer]
            d_ticker_to_color[l_unique_tickers[i]]=newcolor
            pointer = pointer+1

        #align list of colors with dataframe    
        l_tickers = df[self.column_for_colors].tolist()
        l_colors = list()
        for t in l_tickers:
            newcolor = d_ticker_to_color[t]
            l_colors.append(newcolor)
    
        return l_colors
    
    def create_size_list(self,df):
        return (np.log(df[self.column_for_size])+1)

            
    def create_bqp_dg_scatter(self,df):

        self.dataframe=df

        #COLORS = ['#1B84ED', '#CF7DFF', '#FF5A00', '#00D3D6']
        COLORS = self.create_colors_list(df)
        SIZE = self.create_size_list(df)

        # Create scales
        self.scale_x = bqp.LinearScale()
        self.scale_y = bqp.LinearScale()
        self.sc_size = bqp.LinearScale(min=SIZE.min(), max=SIZE.max())
        #self.sc_size = bqp.LinearScale()

        if self.l_metric_names is not None:
            l_metric_options = self.l_metric_names
        else:
            l_metric_options = df.dtypes[df.dtypes!='object'].index.tolist()
        
        if self.default_x_axis is None:
            x_axis_str = l_metric_options[0]
        elif self.default_x_axis in l_metric_options:
            x_axis_str = self.default_x_axis
        else:
            x_axis_str = l_metric_options[0]
            
        if self.default_y_axis is None:
            y_axis_str = l_metric_options[1]
        elif self.default_y_axis in l_metric_options:
            y_axis_str = self.default_y_axis
        else:
            y_axis_str = l_metric_options[1]            
            

        # Create marks
        self.mark_scatter = bqp.Scatter(x=self.dataframe[x_axis_str],
                                   y=self.dataframe[y_axis_str],
                                   scales={'x': self.scale_x, 'y': self.scale_y,'size':self.sc_size},
                                   default_size=200,
                                   marker='circle',
                                   size=SIZE.round(),
                                   colors=COLORS
                                    )

        # Create Axes
        self.axis_x = bqp.Axis(scale=self.scale_x, label=x_axis_str)
        self.axis_y = bqp.Axis(scale=self.scale_y,
                          orientation='vertical',
                          tick_format='0.0f',
                          label=y_axis_str)

        # Create selector
        self.selector = bqp.interacts.BrushSelector(x_scale=self.scale_x,
                                 y_scale=self.scale_y,
                                 marks=[self.mark_scatter])

        # Create Figure
        self.figure = bqp.Figure(marks=[self.mark_scatter],
                            axes=[self.axis_x, self.axis_y],
                            animation_duration=500,
                            layout={'width':'99%', 'height':'400px'},
                            padding_x=0.05,
                            title=self.chart_title,
                            title_style={'font-size': '13px'},
                            padding_y=0.05,
                            interaction=self.selector,
                            fig_margin={'top': 50, 'bottom': 60,
                                        'left': 50, 'right':30})

        # Create dropown widgets
        self.dropdown_x = widgets.Dropdown(description='X axis',
                              #options=dataframe.columns,
                              options=l_metric_options,
                              value=x_axis_str)
        self.dropdown_y = widgets.Dropdown(description='Y axis',
                              #options=dataframe.columns,
                              options=l_metric_options,
                              value=y_axis_str)



        # Bind callback to the dropdown widgets
        self.dropdown_x.observe(self.update_plot, names=['value'])
        self.dropdown_y.observe(self.update_plot, names=['value'])
        self.mark_scatter.observe(self.on_select_scatter, names=['selected'])

        # Create datagrid
        self.datagrid = ipydatagrid.DataGrid(self.dataframe.round(2),
                                             column_widths=self.dg_col_defs,
                                             selection_mode='row',
                                             layout={'height': self.DEFAULT_DG_HEIGHT,
                                                     'width': self.DEFAULT_DG_WIDTH})
        self.datagrid.observe(self.on_click_dg, 'selections')
    
        # Create Box containers
        self.widget_box = widgets.HBox([self.dropdown_x, self.dropdown_y], layout={'margin': '10px'})

        self.figure_box = widgets.VBox([self.figure, self.widget_box])

        self.app_container = widgets.HBox([self.datagrid, self.figure_box],
                             layout={'width':'100%'})

        dummy_event = dict()
        
        self.update_plot(dummy_event)
        # Display the visualization
        return self.app_container