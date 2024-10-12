from ipywidgets import Dropdown, HBox, HTML, IntSlider, IntRangeSlider, FloatSlider, FloatRangeSlider, IntText, FloatText, Label, Textarea, Tab

import ipydatagrid as ipdg
from bqplot import ColorScale, Scale

from layout_setup import _style ,_univ_layout,_label_layout,_sign_layout,_criteria_layout

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class CriteriaWidgets(HBox):
    def __init__(self, label_name, operator, value, max_value=100, min_value=0):
        self.label = Label(label_name, layout=_label_layout)
        self.operator = Dropdown(options=['<','>','='], layout=_sign_layout, value=operator)
        self.value = FloatSlider(value=value, max=max_value, min=min_value, layout=_criteria_layout)
        
        super().__init__(children=[self.label, self.operator, self.value])
        
    def get_label(self):
        return self.label.value
    def get_operator(self):
        return self.operator.value
    def get_value(self):
        return self.value.value



COLS_MAPPING = {
    'Name': ('Description', 'Name'),
    'Country': ('Description','Country'),
    'GICS Sector': ('Description', 'GICS Sector'),
    'BICS Sector': ('Description', 'BICS Sector'),
    'BICS Industry': ('Description', 'BICS Industry'),
    'Price (USD)': ('Market', 'Price (USD)'),
    'EPS FY0': ('Fundamental', 'EPS FY0'),
    'EPS FY1': ('Fundamental', 'EPS FY1'),
    'EPS FY2': ('Fundamental', 'EPS FY2'),
    'Revenue FY0 (in mln USD)': ('Fundamental', 'Revenue FY0 (in mln USD)'),
    'Revenue Growth FY-1/FY0': ('Fundamental', 'Revenue Growth FY-1/FY0'),
    'Revenue Est Growth FY0/FY1': ('Fundamental', 'Revenue Est Growth FY0/FY1'),
    'Dividend Per Sh': ('Fundamental', 'Dividend Per Sh'),
    'Upside (Consensus)': ('Recommendation', 'Upside (Consensus)'),
    'Total Rec': ('Recommendation', 'Total Rec'),
    'Buy Rec': ('Recommendation', 'Buy Rec'),
    'Hold Rec': ('Recommendation', 'Hold Rec'),
    'Sell Rec': ('Recommendation', 'Sell Rec'),
    'Consensus Rating': ('Recommendation', 'Consensus Rating'),
    'ESG MSCI Rating': ('ESG', 'ESG MSCI Rating'),
    'Size': ('Factors', 'Size'),
    'Value': ('Factors', 'Value'),
    'Momentum': ('Factors', 'Momentum'),
    'Volatility': ('Factors', 'Volatility'),
    'Quality': ('Factors', 'Quality'),
    'Size Score': ('Scores', 'Size Score'),
    'Value Score': ('Scores', 'Value Score'),
    'Momentum Score': ('Scores', 'Momentum Score'),
    'Volatility Score': ('Scores', 'Volatility Score'),
    'Quality Score': ('Scores', 'Quality Score'),
    'Composite Score': ('Scores', 'Composite Score')
}

def generate_table(df):

    cols_renderer = {
        ('Market', 'Price (USD)'):ipdg.TextRenderer(format='.2f', horizontal_alignment='center'),
        ('Fundamental', 'EPS FY0'):ipdg.TextRenderer(format='.2f', horizontal_alignment='center'),
        ('Fundamental', 'EPS FY1'):ipdg.TextRenderer(format='.2f', horizontal_alignment='center'),
        ('Fundamental', 'EPS FY2'):ipdg.TextRenderer(format='.2f', horizontal_alignment='center'),
        ('Fundamental', 'Revenue FY0 (in mln USD)'):ipdg.TextRenderer(format=',.2f', horizontal_alignment='center'),
        ('Fundamental', 'Revenue Growth FY-1/FY0'):ipdg.TextRenderer(format='.2%', horizontal_alignment='center'),
        ('Fundamental', 'Revenue Est Growth FY0/FY1'):ipdg.TextRenderer(format='.2%', horizontal_alignment='center'),
        ('Fundamental', 'Dividend Per Sh'):ipdg.TextRenderer(format='.2f', horizontal_alignment='center'),
        ('Recommendation', 'Upside (Consensus)'):ipdg.TextRenderer(format='.2%', horizontal_alignment='center'),
        ('Recommendation', 'Total Rec'): ipdg.TextRenderer(horizontal_alignment='center'),
        ('Recommendation', 'Buy Rec'): ipdg.TextRenderer(format='.2%', horizontal_alignment='center'),
        ('Recommendation', 'Hold Rec'): ipdg.TextRenderer(format='.2%', horizontal_alignment='center'),
        ('Recommendation', 'Sell Rec'): ipdg.TextRenderer(format='.2%', horizontal_alignment='center'),
        ('Recommendation', 'Consensus Rating'):ipdg.TextRenderer(format='.3f', horizontal_alignment='center'),
        ('Factors', 'Size'):ipdg.TextRenderer(format=',.2f', horizontal_alignment='center'),
        ('Factors', 'Value'):ipdg.TextRenderer(format='.2f', horizontal_alignment='center'),
        ('Factors', 'Momentum'):ipdg.TextRenderer(format='.2f', horizontal_alignment='center'),
        ('Factors', 'Volatility'):ipdg.TextRenderer(format='.2f', horizontal_alignment='center'),
        ('Factors', 'Quality'):ipdg.TextRenderer(format='.2f', horizontal_alignment='center'),
        ('Scores', 'Size Score'):ipdg.TextRenderer(format='.3f', horizontal_alignment='center', background_color=ColorScale(min=float(df[('Scores', 'Size Score')].dropna().min()), max=float(df[('Scores', 'Size Score')].dropna().max()), scheme='RdYlGn')),
        ('Scores', 'Value Score'):ipdg.TextRenderer(format='.3f', horizontal_alignment='center', background_color=ColorScale(min=float(df[('Scores', 'Value Score')].dropna().min()), max=float(df[('Scores', 'Value Score')].dropna().max()), scheme='RdYlGn')),
        ('Scores', 'Momentum Score'):ipdg.TextRenderer(format='.3f', horizontal_alignment='center', background_color=ColorScale(min=float(df[('Scores', 'Momentum Score')].dropna().min()), max=float(df[('Scores', 'Momentum Score')].dropna().max()), scheme='RdYlGn')),
        ('Scores', 'Volatility Score'):ipdg.TextRenderer(format='.3f', horizontal_alignment='center', background_color=ColorScale(min=float(df[('Scores', 'Volatility Score')].dropna().min()), max=float(df[('Scores', 'Volatility Score')].dropna().max()), scheme='RdYlGn')),
        ('Scores', 'Quality Score'):ipdg.TextRenderer(format='.3f', horizontal_alignment='center', background_color=ColorScale(min=float(df[('Scores', 'Quality Score')].dropna().min()), max=float(df[('Scores', 'Quality Score')].dropna().max()), scheme='RdYlGn')),
        ('Scores', 'Composite Score'):ipdg.TextRenderer(format='.3f', horizontal_alignment='center', background_color=ColorScale(min=float(df[('Scores', 'Composite Score')].dropna().min()), max=float(df[('Scores', 'Composite Score')].dropna().max()), scheme='RdYlGn'))
    }
    return ipdg.DataGrid(
        dataframe=df.reset_index().rename(columns={'ID':('Description', 'Ticker')}),
        base_column_size=100,
        base_row_header_size=120,
        renderers=cols_renderer,
        selection_mode='cell',
        header_visibility='column'
    )
    
def generate_return_graph(df_return, ticker, industry):
    px_fig = go.Figure(
        data=[
            go.Scatter(name='6M Cumul. Return', x=df_return.index, y=df_return['6M Cumul. Return'], marker_color='white'),
            go.Scatter(name='6M Cumul. Return (Industry Avg)', x=df_return.index, y=df_return['6M Cumul. Return (Industry Avg)'], marker_color='RoyalBlue'),
        ]
    )

    px_fig.update_layout(template='plotly_dark',title='{} 6M Return vs {} Average'.format(ticker, industry),legend_orientation='h')
    return go.FigureWidget(px_fig)

def generate_rec_graph(df_rec, ticker):
    rec_fig = go.Figure(
        data=[
            go.Scatter(name='Target Price', x=df_rec.index, y=df_rec['Target Price'], yaxis='y', marker_color='white'),
            go.Bar(name='Buy Rec', x=df_rec.index, y=df_rec['Buy Rec'], yaxis='y2', offsetgroup=2, marker_color='green'),
            go.Bar(name='Hold Rec', x=df_rec.index, y=df_rec['Hold Rec'], yaxis='y2', offsetgroup=2, marker_color='yellow'),
            go.Bar(name='Sell Rec', x=df_rec.index, y=df_rec['Sell Rec'], yaxis='y2', offsetgroup=2, marker_color='red'),
        ],
        layout={
            'yaxis': {'title': 'Target Price','overlaying': 'y2'},
            'yaxis2': {'title': 'Recommendation', 'side': 'right'}
        },
    )

    rec_fig.update_layout(barmode='stack', template='plotly_dark',title='{} Recommendation'.format(ticker),legend_orientation='h')
    return go.FigureWidget(rec_fig)

def generate_earnings_graph(df_eps, ticker):
    eps_fig = go.Figure(
        data=[
            go.Bar(name='EPS', x=df_eps.index, y=df_eps['EPS'], marker_color='SeaGreen'),
            go.Bar(name='EPS Est.', x=df_eps.index, y=df_eps['EPS Est.'], marker_color='LightGray'),
        ],

    )

    eps_fig.update_layout(barmode='group', template='plotly_dark',title='{} Earnings'.format(ticker),legend_orientation='h')
    return go.FigureWidget(eps_fig)

def generate_factors_distribution(df):
    factors_headers = [ (cat, fld) for cat, fld in df.columns if cat=='Factors']

    fig = make_subplots(rows=1, cols=len(factors_headers))

    for idx,factor in enumerate(factors_headers):
        cat, fld = factor
        fig.add_trace(
            go.Box(name=fld, y=df[(cat, fld)]),
            row=1, col=idx+1
        )

    fig.update_layout(template='plotly_dark',title='Factors Distribution',showlegend=False, width=1000, height=500, autosize=False)
    return go.FigureWidget(fig)

def get_scatter(data, group, score_x, score_y):
    group_index = ('Description',group)
    x_score = ('Scores', score_x)
    y_score = ('Scores', score_y)

    df = data.groupby(group_index).agg('mean').round(2).reset_index()
    df_count = data.groupby(group_index).agg('count').reset_index()
    df_count['Size'] =  20+20*(df_count[('Description','Name')] - df_count[('Description','Name')].min())/(df_count[('Description','Name')].max() - df_count[('Description','Name')].min())
    color_list = (px.colors.diverging.balance*2)[:len(df_count)]
    fig_scatter = go.Figure(
        data=[
            go.Scatter(
                name=row[group_index],
                marker=dict(
                    size=df_count[df_count[group_index]==row[group_index]]['Size'],
                    color=color_list[idx],
                    line=dict(
                        width=2,
                        color='DarkSlateGrey')
                ),
                x=[row[x_score]],
                y=[row[y_score]]
            )
            for idx, row in df.iterrows()
        ]

    )
    fig_scatter.update_layout(template='plotly_dark', width=1000, height=500)
    return go.FigureWidget(fig_scatter)