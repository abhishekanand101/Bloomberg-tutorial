import plotly.graph_objects as go
import ipywidgets as ipw
import pandas as pd
import numpy as np

class  GOInteractiveScatterPlot():

    def __init__(self,df,color_column_name=None,**fig_params):
        self.df = df.select_dtypes('float64')
        global first_scatter
        first_column_name = self.df.columns[0]
        if not color_column_name:
            color_column_name = first_column_name
        first_scatter=go.Scatter(x = self.df[first_column_name],y = self.df[first_column_name], mode = 'markers',
                                         marker= {'color': self.df[color_column_name],'colorscale':[[0,'red'],[1,'green']] },
                                     hovertext = self.df.index
                                        )
        self.widgets = {}
        self.widgets['results_scatter_figure']= go.FigureWidget([first_scatter],
                                                                layout=go.Layout(template='plotly_dark',dragmode='select'))
        self.widgets['results_scatter_figure'].update_layout(**fig_params)
        
        self.scatter = self.widgets['results_scatter_figure'].data[0]
        self.axis_dropdowns = ipw.interactive(self.update_axes, 
                                              yaxis = self.df.select_dtypes('float64').columns[::-1], 
                                              xaxis = self.df.select_dtypes('float64').columns)
        
        self.widgets['InteractiveScatter'] = ipw.VBox([self.widgets['results_scatter_figure'],self.axis_dropdowns])


    def update_axes(self,xaxis, yaxis):
        self.scatter.x = self.df[xaxis]
        self.scatter.y = self.df[yaxis]
        self.widgets['results_scatter_figure'].update_layout(xaxis_title=xaxis, yaxis_title=yaxis)
    
        
    def show(self):
        return self.widgets['InteractiveScatter']


