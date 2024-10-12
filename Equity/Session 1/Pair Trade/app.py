# importing libraries for data transformation/ manipulation 
import numpy as np
import pandas as pd
from datetime import date, timedelta
import traceback
from ast import literal_eval as make_tuple

# importing DataModel, Backtestingodel, Cointmodel and UniversePicker class
from DataModel import DataModel
from BacktestingModel import BacktestingModel
from CointModel import CointModel
from universe import * 

# importing ibraries for app visuals 
import bqplot as bqp
from bqplot.interacts import IndexSelector
from ipydatagrid import DataGrid, TextRenderer
from ipywidgets import Layout, Button, HTML, DatePicker, VBox, HBox, Text, Tab, Box, Dropdown, Textarea

# styling for input boxes & chart visualisations 
_LAY_MED = {'width':'130px'}
_LAY_DATE = {'width': '150px'}

# styling for chart visualisations 
box_layout = Layout(display='flex',
                flex_flow='column',
                align_items='center',
                width='100%')

# styling for results table
_RENDERERS_cointpairs = {
    'Independent': TextRenderer(horizontal_alignment='center'),
    'Dependent': TextRenderer(horizontal_alignment='center'),
    'Ratio': TextRenderer(format='.2f', horizontal_alignment='center'), # added 
    'PnL Pcts': TextRenderer(format='.2%', horizontal_alignment='center'),
    'Win Pcts': TextRenderer(format='.2%', horizontal_alignment='center'),
    'Num Trades': TextRenderer(horizontal_alignment='center'),
    'Max Win': TextRenderer(format='.2f', horizontal_alignment='center'), 
    'Max Loss': TextRenderer(format='.2f', horizontal_alignment='center'),
}
_RENDERERS_teststats = {
    '1%': TextRenderer(format='.2f', horizontal_alignment='center'),
    '5%': TextRenderer(format='.2f', horizontal_alignment='center'),
    '10%': TextRenderer(format='.2f', horizontal_alignment='center'),
    'Test Stat': TextRenderer(format='.2f', horizontal_alignment='center'),
}

# error traceback & loading icon & status 
errors = []
_loading = '<i class="fa fa-spinner fa-spin fa-2x fa-fw" style="color:ivory;"></i>'
status = HTML()

# Text for instructions 
instructions = '''
<div style="color:ivory;background-color:DimGray;padding:10px;border-radius: 25px;">
    <span style="font-weight:bold"> Description: </span><br>
    This sample application allows you to :
    <ul>
        <li>Screen an index or a portfolio for cointegrated pairs.</li>
        <li>View key backtesting metrics of curated cointegrated pairs.</li>
    </ul>
    <span style="font-weight:bold"> Instructions: </span>
    <ul>
        <li>Input the index or your list of tickers in the <span style="font-style:italic; font-weight:bold">Universe</span> section.<br></li>
        <li>Apply different filters to carry out the Engle-Granger Cointegration Test & Backtesting.<br></li>
        <li>Hit the <span style="font-style:italic; font-weight:bold"><u>Run</u></span> button to update your analysis and see your results in the <span style="font-style:italic; font-weight:bold">Results</span> section.<br></li>
    </ul>
   
</div>'''

# Functionality: DateModel, CointModel, BacktestingModel and UniversePicker class 
data_model = DataModel()
coint_model = CointModel()
bt_model = BacktestingModel()
universe_picker = UniversePicker()

# UI component: universe 
univ_comp = universe_picker.show()

# UI component: start and end date
st_date_comp = DatePicker(value=date.today()-timedelta(days=365*5), layout=_LAY_DATE)
end_date_comp = DatePicker(value=date.today(), layout=_LAY_DATE)

# UI component: initial capital, significance level, trading signal std 
init_cap = Text(value='10000', layout=_LAY_MED)
sig_lvl_comp = Dropdown(options=['1%', '5%', '10%','100%'], value='5%', layout=_LAY_MED)
std_comp = Dropdown(options=['1', '1.5', '2'], value='1.5', layout=_LAY_MED)

# UI component: run button 
run_button = Button(description='Run', button_style='info')

# UI components: universe,dates and conditions components 
univ_box = VBox([univ_comp])
conds_box = VBox([
    HTML('<h3>Conditions</h3>'),
    HBox([
        VBox([HTML('<h5>Initial Capital</h5>'), init_cap]),
        VBox([HTML('<h5>Confidence Level</h5>'),  sig_lvl_comp]),
        VBox([HTML('<h5>Trading Signals</h5>'), std_comp]),
        ])  
])
dates_box = VBox([
    HTML('<h3>Time Frame</h3>'),
    HBox([st_date_comp, end_date_comp])
])

# UI component: results 
results_grid = VBox()
results_chart = VBox()

data, coint_pairs, trade_info, bt_metrics = None, None, None, None

# Charting method to update chart 
def charts_update(event):
    refresh_charts(event['new'])
    
# Charting method to create residual z-score chart  
def zscore_chart(key_pair_tup):
    zscores = bt_model.zscores.get(key_pair_tup)
    dates = data_model.dates
    pos_std = [bt_model.std, ] * len(dates)
    neg_std = [-bt_model.std, ] * len(dates)
    zero_mean = [0, ] * len(dates)
    
    # dataframe 
    dataframe = pd.DataFrame(np.column_stack([zscores, pos_std, neg_std, zero_mean]),
                index=dates,
                columns=['Z Scores', '+ STD', '- STD', 'Long Term Mean'])

    # Create scales
    scale_x, scale_y = bqp.DateScale(), bqp.LinearScale()
    
    # Create the Lines mark
    mark_line = bqp.Lines(x=dataframe.index,
                     y=[dataframe[col] for col in dataframe.columns],
                          scales={'x': scale_x, 'y': scale_y},
                          colors=['#1B84ED', '#CF7DFF', '#FF5A00', '#00D3D6'],
                          labels=dataframe.columns.tolist(),
                          display_legend=True)
    
    # Create Axes
    axis_x = bqp.Axis(scale=scale_x, label='Dates', label_color='ivory')
    axis_y = bqp.Axis(scale=scale_y,
                  orientation='vertical',
                  side='right',
                  label_offset='4em')
    
    # Create Figure
    figure = bqp.Figure(marks=[mark_line],
                    axes=[axis_x, axis_y],
                    layout={'width':'800px', 'height': '400px'},
                    title_style={'font-size': '16px'},
                    legend_location='top-left',
                    interaction=IndexSelector(scale=scale_x,
                                               marks=[mark_line]),
                    legend_style={'stroke': 'none', 'font-size': '10px'},
                        fig_margin={'top': 10, 'bottom': 30,
                                'left': 10, 'right': 80})
    
    return figure

# Chart text to expain the residual z-score chart
graph_txt = '''
    <p style="color:grey;"><i>For any pair of cointegrated tickers, we compute a rolling z-score based on the 
    time series of residuals obtained.The lookback period is determined by the half-life of the mean reversion 
    (Note: there is data leakage here). </i></p> 
    <p style="color:grey;"><i>When Z-score crosses upper threshold, go short and hold position till mean reversion:
            <br> &emsp; - Sell depedent ticker, Buy independent ticker
    <i>
    <i><br>When Z-score crosses lower threshold, go long and hold position till mean reversion:
            <br> &emsp; - Sell indepedent ticker, Buy dependent ticker
    <i></p>'''

# Charting method to create spread chart 
def spread_chart(key_pair_tup):
    all_spread = bt_model.all_spreads.get(key_pair_tup)
    dates = data_model.dates
    
    dataframe = pd.DataFrame(all_spread,
                index=dates,
                columns=['Spreads'])
    
    # Create scales
    scale_x = bqp.DateScale()
    scale_y = bqp.LinearScale()
    
    # Create the Lines mark
    mark_line = bqp.Lines(x=dataframe.index,
                      y=[dataframe[col] for col in dataframe.columns],
                      scales={'x': scale_x, 'y': scale_y},
                      colors=['#1B84ED'],
                      labels=dataframe.columns.tolist(),
                      display_legend=True)
    # Create Axes
    axis_x = bqp.Axis(scale=scale_x, label='Dates', label_color='ivory')
    axis_y = bqp.Axis(scale=scale_y,
                  orientation='vertical',
                  side='right',
                  label_offset='4em')
    # Create Figure
    figure = bqp.Figure(marks=[mark_line],
                    axes=[axis_x, axis_y],
                    layout={'width':'800px', 'height': '400px'},
                    title_style={'font-size': '16px'},
                    legend_location='top-left',
                    interaction=IndexSelector(scale=scale_x,
                                              marks=[mark_line]),
                    legend_style={'stroke': 'none'},
                    fig_margin={'top': 10, 'bottom': 30,
                                'left': 10, 'right': 80})
    
    return figure

# Charting method to create capital chart 
def capital_chart(key_pair_tup, trade_info):
    capital_data = trade_info.get('cap_vals').get(key_pair_tup)
    dates = trade_info.get('trade_dates').get(key_pair_tup)
    dates = [x[1] for x in dates]
    dates.insert(0,data.get('dates')[0])
    
    dataframe = pd.DataFrame(capital_data,
                index=dates,
                columns=['Capital'])
    
    # Create scales
    scale_x = bqp.DateScale()
    scale_y = bqp.LinearScale()
    
    
    # Create the Lines mark
    mark_line = bqp.Lines(x=dataframe.index,
                      y=[dataframe[col] for col in dataframe.columns],
                      scales={'x': scale_x, 'y': scale_y},
                      colors=['#1B84ED'],
                      labels=dataframe.columns.tolist(),
                      y_legend=True)
    # Create Axes
    axis_x = bqp.Axis(scale=scale_x, label='Dates', label_color='ivory')
    axis_y = bqp.Axis(scale=scale_y,
                  orientation='vertical',
                  side='right',
                  label_offset='4em')
    # Create Figure
    figure = bqp.Figure(marks=[mark_line],
                    axes=[axis_x, axis_y],
                    # title='Capital',
                    layout={'width':'800px', 'height': '400px'},
                    title_style={'font-size': '16px'},
                    legend_location='top-left',
                    interaction=IndexSelector(scale=scale_x,
                                              marks=[mark_line]),
                    legend_style={'stroke': 'none'},
                    fig_margin={'top': 10, 'bottom': 30,
                                'left': 10, 'right': 80})
    
    return figure

# Charting method to refresh charts dynamically based on tickers pair selected in pair_select 
def refresh_charts(key_pair_tup):
    # transform string to a tuple 
    key_pair_tup = make_tuple(key_pair_tup)
    # retrieve and apply data transformation to engle-granger stats from coint_model 
    adf_table = {k:[v] for k,v in coint_model.residual_stats.get(key_pair_tup).items()}
    adf_test_results = DataGrid(
        pd.DataFrame.from_dict(adf_table),
        base_row_size=20,base_column_size=80,base_column_header_size=20, base_row_header_size=60, 
        header_visibility='column', renderers=_RENDERERS_teststats, 
        layout={'height': '50px', 'width': '320px'}    
    )
    
    # refresh all the charts and test stat table 
    charts = VBox([
        HTML('<h1>                  </h1>'),
        HTML("<h5><font color='ivory'>Residual Z-Score Chart</h5>"),
        zscore_chart(key_pair_tup),
        HTML(graph_txt),
        HTML("<h5><font color='ivory'>Spread Chart</h5>"),
        spread_chart(key_pair_tup),
        HTML("<h5><font color='ivory'>Engle-Granger Co-integration Test</h5>"),
        adf_test_results,
        HTML("<h1>                     </h1>"),
        HTML("<h5><font color='ivory'>Capital Chart</h5>"),
        capital_chart(key_pair_tup, trade_info)
    ], layout=box_layout)
    
    results_chart.children = [charts]

# Method to update screening dynamically based on universe, time frame and conditions   
def refresh(*args, **kwargs):
    
    global data, coint_pairs, trade_info, bt_metrics
    
    try: 
        status.value = _loading
        run_button.description = 'Loading'
        run_button.disabled = True
        
        # initialise all models for screening 
        data_model.initialise_model(universe_picker.get_universe(), st_date_comp.value, end_date_comp.value)
        data = data_model.run()
        coint_model.initialise_model(data, sig_lvl_comp.value)
        coint_pairs = coint_model.screen_univ()
        bt_model.initialise_model(coint_pairs, data, float(init_cap.value), float(std_comp.value))
        trade_info = bt_model.run()
        bt_metrics = bt_model.compute_bt_metrics()

        # display quality cointegrated pairs in table 
        display_results(coint_pairs, trade_info, bt_metrics)
    
    except Exception as e:
        # if error, there's no co-integrated pairs 
        results_grid.children = [HTML('No cointegrated pair')]
        results_chart.children = []
        errors.append(e)
        errors.append(traceback.format_exc())
    
    status.value = ''
    run_button.description = 'Run'
    run_button.disabled = False

# Method to display all quality cointegrated pairs in table 
def display_results(coint_pairs, trade_info, bt_metrics):
    
    global key_pairs 
    key_pairs = list(map(str, bt_metrics.get('pnl_pcts').keys()))
    indep_ticker, dep_ticker = [], []
    pnl_pcts, win_pcts = [], []
    num_trades = []
    max_wins, max_losses = [], []
    hedge_ratio = []
    res_table = {}
        
    for pair in key_pairs:
        pair = make_tuple(pair)
        indep_ticker.append(pair[0])
        dep_ticker.append(pair[1])
        pnl_pcts.append(bt_metrics.get('pnl_pcts').get(pair))
        win_pcts.append(bt_metrics.get('win_pcts').get(pair))
        num_trades.append(bt_metrics.get('tot_trades').get(pair))
        max_wins.append(bt_metrics.get('max_wins').get(pair))
        max_losses.append(bt_metrics.get('max_losses').get(pair))
        hedge_ratio.append(coint_pairs.get(pair)[0]) 
            
        res_table = {'Independent': indep_ticker, 'Dependent': dep_ticker, 'Ratio': hedge_ratio,
                    'PnL Pcts': pnl_pcts, 'Win Pcts': win_pcts,
                    'Num Trades': num_trades, 'Max Win': max_wins,
                    'Max Loss': max_losses}
    
    results = DataGrid(
            pd.DataFrame.from_dict(res_table),
            base_row_size=40,base_column_size=100,base_column_header_size=30, base_row_header_size=80, 
            header_visibility='column', renderers=_RENDERERS_cointpairs, 
            layout={'height': '{}px'.format(len(pd.DataFrame.from_dict(res_table))*50+50), 
                   'width': '700px'}    
    )
    
    results_centered = VBox(children=[HTML("<h5><font color='ivory'>Quality Co-integrated Pairs</h5>"), results], layout=box_layout)

    global pair_select
    
    pair_select = Dropdown(options=sorted(key_pairs))
    results_grid.children = [results_centered, HTML("<h3>Visualisations of Key Backtesting Metrics</h3>"), pair_select] 
    refresh_charts(pair_select.value)
    pair_select.observe(charts_update, 'value')
    
# Text for Methodology page 
method = '''
<div style="color:ivory;background-color:DimGray;padding:10px;border-radius: 25px;">
    <span style="font-weight:bold"> Detailed Methodology: </span><br>
    <ul>
        <span style="font-weight:bold"> Key idea </span><br>
        The idea of Pairs Trading is to study a historical relationship and spot opportunities that arise when the
        stationary relationship between a pair of tickers breaks down. We can then buy the implied undervalued ticker while 
        shorting the overvalued ticker in attempt to revert to the original relationship. <br>
        
        <span style="font-weight:bold"> For any pair of tickers: </span><br>
        <li> The app first calculates the Ordinary Least Squares Regression (OLS) for 
        the two natural logarithmic time series and obtain the coefficient, constant and a time series of residuals. </li>
        <li> The Augmented Dickey-Fuller Test (ADF) is then performed on the residuals to screen for stationarity and subsequently co-integration. </li>
        
        <span style="font-weight:bold"> For co-integrated ticker pairs: </span><br>
        <li> Spread = log(Dependent Ticker Price) - hedge ratio * log(Independent Ticker Price), where hedge ratio is the OLS coefficient.</li>
        <li> The app computes a rolling z-score of the time series of residuals. Trade entry and exit points are calculated where the residual 
        moves above or below the standard deviation specified by the user and exits the strategy once the residual reaches 
        near the mean of the residual (specified as within +/- 0.5 std here). </li>
        <li> Key backtesting metrics (percentage of pnl, winning trades etc) are generated. </li>
    </ul>
    
</div>'''

# UI component: Screening Page
controls = VBox([
    HTML('<h1>Pairs Trading Application</h1>'),
    HBox([VBox([univ_box, conds_box]), dates_box]),
    HTML('<h1>                  </h1>'),
    HBox([run_button, status]),
    HTML('<h3>Results</h3>'),
    results_grid,
    HTML('<h1>                  </h1>'),
    results_chart
])

# UI component: Methodology Page 
details = VBox([
    HTML('<h1>Detailed Methodology</h1>'),
    HTML(method)
])

# Attaching callback to Run Button
run_button.on_click(refresh)
