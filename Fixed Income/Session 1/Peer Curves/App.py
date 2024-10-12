import bql
import pandas as pd
import os
import datetime
import ipywidgets as widgets
import bqwidgets
import collections
import sys
from UtilityWidgets import ApplicationLogger
from IPython.display import display
import BQL_Util
import UI

# #Supress BQL Errors
# f = open(os.devnull, 'w')
# sys.stderr = f

class App():
    def __init__(self, bql_util=None, ui=None):
        if bql_util is None:
            self.bql_util = BQL_Util.BQL_Util(app=self)
        else:
            self.bql_util = bql_util
            self.bql_util.app = self

        self._load_settings()

        if ui is None:
            self.ui = UI.UI(app=self)
        else:
            self.ui = ui


    ####IO
    def _load_settings(self):
        ##load in config for top_level_summary
        self._load_top_level_summary()
        self._load_mat_buckets()
        self._load_rtg_buckets()
        self._load_fundamental_settings()
        self._load_fundamental_financials_settings()
        self._load_senior_sub_settings()
        self._load_metric_settings()
        self.dict_data=collections.OrderedDict()

    def _load_top_level_summary(self):
        path = 'settings{}config_top_level_summary.csv'.format(os.sep)
        try:
            df = pd.read_csv(path)
            self.df_config_top_level_summary=df
            self.bql_util.validate_top_level_summary_code()
            self.log_message('Loaded config file for top level summary with {} fields'.format(len(df)))
        except:
            self.log_message('Unable to read config file for top level summary: {}'.format(path),color='red')
            self.df_config_top_level_summary=pd.DataFrame()            


    def _get_top_level_summary_data(self, ticker):
        df = self.bql_util.retrieve_top_level_summary_data(ticker)
        return df


    def _load_mat_buckets(self):
        path = 'settings{}config_mat_buckets.csv'.format(os.sep)
        try:
            df = pd.read_csv(path)
            self.df_config_mat_buckets=df
            # self.bql_util.validate_top_level_summary_code()
            self.log_message('Loaded config file for maturity buckets with {} rows'.format(len(df)))
        except:
            self.log_message('Unable to read config file for maturity buckets: {}'.format(path),color='red')
            self.df_config_mat_buckets=pd.DataFrame()    

    def _load_fundamental_financials_settings(self):
        path = 'settings{}config_fundamentals_financials.csv'.format(os.sep)
        try:
            df = pd.read_csv(path)
            self.df_config_fundamentals_financials=df
            # self.bql_util.validate_top_level_summary_code()
            self.log_message('Loaded config file for Financial fundamentals with {} fields'.format(len(df)))
        except:
            self.log_message('Unable to read config file for Financial fundamental fields: {}'.format(path),color='red')
            self.df_config_fundamentals_financials=pd.DataFrame()                  

    def _load_fundamental_settings(self):
        path = 'settings{}config_fundamentals.csv'.format(os.sep)
        try:
            df = pd.read_csv(path)
            self.df_config_fundamentals=df
            # self.bql_util.validate_top_level_summary_code()
            self.log_message('Loaded config file for fundamentals with {} fields'.format(len(df)))
        except:
            self.log_message('Unable to read config file for fundamental fields: {}'.format(path),color='red')
            self.df_config_fundamentals=pd.DataFrame()                       


    def _load_rtg_buckets(self):
        path = 'settings{}config_rtg_buckets.csv'.format(os.sep)
        try:
            df = pd.read_csv(path)
            self.df_config_rtg_buckets=df
            # self.bql_util.validate_top_level_summary_code()
            self.log_message('Loaded config file for ratings buckets with {} mappings'.format(len(df)))
        except:
            self.log_message('Unable to read config file for ratings buckets: {}'.format(path),color='red')
            self.df_config_rtg_buckets=pd.DataFrame()         

    def _load_senior_sub_settings(self):
        self.SENIOR_STR_LIST=['1st lien','1.5 Lien','2nd lien','3rd lien','Asset Backed','Secured','Sr Unsecured']
        self.SUB_STR_LIST=['Sr Subordinated','Subordinated','Jr Subordinated','Unsecured']

    def _load_metric_settings(self):
        path = 'settings{}config_metric_defs.csv'.format(os.sep)
        try:
            df = pd.read_csv(path)
            self.df_config_metrics=df
            # self.bql_util.validate_top_level_summary_code()
            self.log_message('Loaded config file for metric definitions with {} metrics'.format(len(df)))
        except:
            self.log_message('Unable to read config file for metric definitions: {}'.format(path),color='red')
            self.df_config_metrics=pd.DataFrame()         

    def _get_fundamentals_for_peers(self, ticker):
        """ 
        Summary: Retrieve fundamental data for peers of company
        Input: ticker
        Output: Data Frame, indexed by ticker, for variety of fundamental fields. Peers are determined as by membership 
            in GICS_INDUSTRY_SUB_GROUP, in the same country, and within a two-tiered matching range for market cap

        """
        df_top_level_summary = self.dict_data['top_level_summary_data']
        country = df_top_level_summary.loc['Country'].iloc[0]
        gics_subindustry = df_top_level_summary.loc['GICS Sub-Industry'].iloc[0]
        gics_sector = df_top_level_summary.loc['GICS Sector'].iloc[0]
        cur_mkt_cap = df_top_level_summary.loc['Market Cap (B)'].iloc[0]
        if cur_mkt_cap < 2:
            min_mkt_cap_b = 0.25
            max_mkt_cap_b = 10
        elif cur_mkt_cap < 15:
            min_mkt_cap_b = 0.5
            max_mkt_cap_b = 50
        else:
            min_mkt_cap_b = 1.5
            max_mkt_cap_b = None

        ##contruct BQL query for 
        try:
            df_fundamental_data = self.bql_util.retrieve_fundamental_data(ticker=ticker, country=country, min_mkt_cap_b=min_mkt_cap_b, max_mkt_cap_b=max_mkt_cap_b, gics_subindustry=gics_subindustry, gics_sector=gics_sector)
        except:
            self.log_message('Error retrieving fundamental data for {}'.format(ticker),preserve_spinner=True)
            return None

        description = 'Fundamentals on {}'.format(gics_subindustry)
        d = dict()
        d['description']=description
        d['df']=df_fundamental_data

        return d

    def _get_list_of_date_str_for_trend(self):
        l_date_str = list()
        l_date_str.append("-0D")
        l_date_str.append("-1W")
        l_date_str.append("-2W")
        l_date_str.append("-1M")
        l_date_str.append("-2M")
        l_date_str.append("-3M")
        l_date_str.append("-4M")
        l_date_str.append("-5M")
        l_date_str.append("-6M")
        l_date_str.append("-7M")
        l_date_str.append("-8M")
        l_date_str.append("-9M")        
        l_date_str.append("-10M")
        l_date_str.append("-11M")
        l_date_str.append("-12M")
        return l_date_str

    def lookup_bql_str_for_metric(self, metric_str):
        df = self.df_config_metrics
        if df is None or len(df)==0:
            return None
        ser = df[df['name']==metric_str].iloc[0]
        return ser['bql_string']

    def get_list_of_metric_names(self):
        df = self.df_config_metrics
        if df is None or len(df)==0:
            return None        
        return df['name'].values.tolist()


    def compute_drilldown(self, ticker, mat_str, univ_str, univ_selector_str,index_str,seniority_str, ccy_str,max_num_results=100):

        ##validate ticker
        if not self.bql_util._ticker_is_valid(ticker):
            self.log_message("Ticker '{}' is not formatted properly".format(ticker),color='yellow')
            return

        self.log_message('Computing drilldown for ticker: {}, maturity: {}, universe: {}, comparison universe: {}, index: {}, seniority: {}'.format(ticker, mat_str, univ_str, univ_selector_str, index_str, seniority_str),spinner=True)
        self.ui.drilldown_output_box.children=[self.ui.spinner_box]

        if 'top_level_summary_data' not in self.dict_data.keys():
            top_level_summary_data = self._get_top_level_summary_data(ticker)
            self.dict_data['top_level_summary_data']=top_level_summary_data


        #get parameters from top level summary for drilldown query
        df_top_level_summary = self.dict_data['top_level_summary_data']
        country = df_top_level_summary.loc['Country'].iloc[0]
        sp_rating = df_top_level_summary.loc['S&P Rating'].iloc[0]
        rating_bucket = self.df_config_rtg_buckets[self.df_config_rtg_buckets['sp_rtg']==sp_rating]['bucket'].iloc[0]
        sector = df_top_level_summary.loc['BICS Level 1 Sector'].iloc[0]
        industry_group = df_top_level_summary.loc['BICS Level 2 Industry Group'].iloc[0]        

        df = self.bql_util.query_drilldown(ticker=ticker, mat_str=mat_str, univ_str=univ_str,univ_selector_str=univ_selector_str,index_str=index_str,seniority_str=seniority_str, country=country, rating_bucket=rating_bucket,sector=sector,industry_group=industry_group, ccy_str=ccy_str, max_num_results=max_num_results)

        if df is not None:
            dict_drilldown=dict()
            dict_drilldown['df']=df
            dict_drilldown['ticker']=ticker
            dict_drilldown['mat_str']=mat_str
            dict_drilldown['univ_str']=univ_str
            dict_drilldown['univ_selector_str']=univ_selector_str
            dict_drilldown['index_str']=index_str
            dict_drilldown['seniority_str']=seniority_str
            dict_drilldown['max_num_results']=max_num_results
            dict_drilldown['country']=country
            dict_drilldown['rating_bucket']=rating_bucket
            dict_drilldown['sector']=sector
            dict_drilldown['industry_group']=industry_group

            self.dict_data['drilldown'] = dict_drilldown
            self.log_message('Retrieved drilldown data with {} items'.format(len(df)))
        else:
            self.log_message('Did not retrieve any data for drilldown')









    def _get_trend_data(self, mat_bucket_str, ticker, seniority_str, metric_str, ccy_str=None):
        """
        Summary: Constructs trend data for input ticker and maturity bucket
        Input: ticker (string) and maturity bucket (string)
        Output: 
            Dictionary of two data frame. {"OAS":df_oas, "YTW":df_ytw}
            Each DataFrame has a column corresponding to each universe that is run (e.g. All UTX Bonds, or all BBB rated Bonds), 
                and with an index of the historical date that the data is from
        """
        df_top_level_summary = self.dict_data['top_level_summary_data']
        country = df_top_level_summary.loc['Country'].iloc[0]
        sp_rating = df_top_level_summary.loc['S&P Rating'].iloc[0]

        if sp_rating is None:
            company_name = df_top_level_summary.loc['Name'][0]
            self.log_message('{} does not have a S&P Rating. Skipping Term Structure retrieval'.format(company_name),preserve_spinner=True)
            return None
        rating_bucket = self.df_config_rtg_buckets[self.df_config_rtg_buckets['sp_rtg']==sp_rating]['bucket'].iloc[0]
        sector = df_top_level_summary.loc['BICS Level 1 Sector'].iloc[0]
        industry_group = df_top_level_summary.loc['BICS Level 2 Industry Group'].iloc[0]

        dates_for_analysis = self._get_list_of_date_str_for_trend()

        #starting_univ
        starting_univ_str=None
        if self.ui.univ_radio.value=='Index':
            starting_univ_str = self.ui.index_univ_text_elt.value



        #construct list of tuples for each request date, bql code for OAS
        self.tup_metric = list()
        df = self.df_config_metrics
        dt_bql_str_root = df[df['name']==metric_str].iloc[0]['bql_str_parametrized_date']
        for date_str in dates_for_analysis:
            dt_bql_str = dt_bql_str_root.format(date_str)
            new_tup = (date_str, dt_bql_str)
            self.tup_metric.append(new_tup)

        # self.tup_oas_bql = list()
        # for date_str in dates_for_analysis:
        #     dt_bql_str = "bq.func.avg(bq.func.group(bq.data.spread(spread_type='oas',fill='prev',dates='{}')))".format(date_str)
        #     # dt_bql_code = eval(dt_bql_str)
        #     new_tup = (date_str, dt_bql_str)
        #     self.tup_oas_bql.append(new_tup)

        # #construct list of tuples for each request date, bql code for YTW
        # self.tup_ytw_bql = list()
        # for date_str in dates_for_analysis:
        #     dt_bql_str = "bq.func.avg(bq.func.group(bq.data.yield_(yield_type='ytw',fill='prev',dates='{}')))".format(date_str)
        #     # dt_bql_code = eval(dt_bql_str)
        #     new_tup = (date_str, dt_bql_str)
        #     self.tup_ytw_bql.append(new_tup)


        metric_info = dict()
        metric_info['Name']=metric_str
        metric_info['tups']=self.tup_metric
        # if metric_str=='OAS':
        #     metric_info['tups']=self.tup_oas_bql
        # elif metric_str=='YTW':
        #     metric_info['tups']=self.tup_ytw_bql
        # else:
        #     metric_info['tups']=None

        # print('metric_info: {}'.format(metric_info))

        self.tuple_trend_reqs=self.bql_util.construct_trend_oas_ytw_requests(mat_bucket_str = mat_bucket_str, ticker=ticker, country_iso=country, rating_bucket=rating_bucket, sector=sector, industry_group=industry_group, base_univ_start=starting_univ_str, metric_info=metric_info, seniority_str=seniority_str, ccy_str=ccy_str)


        ##next need to execute asynchronously the requests in list. 
        # od_univs = collections.OrderedDict()
        # od_flds = collections.OrderedDict()
        # for elt in self.tuple_trend_reqs:
        #     elt_info=elt[0]
        #     for metric_name in elt_info['Metric Names']:
        #         od_flds[metric_name]=1
        #     od_univs[elt_info['Universe Label']]=1
        # str_unique_univs = str(list(od_univs.keys()))
        # str_unique_fields = str(list(od_flds.keys()))

        self.log_message('Querying BQL with {} total requests, with {} fields each'.format(len(self.tuple_trend_reqs),len(self.tup_metric)),preserve_spinner=True)


        try:
            self.l_df, self.l_dict_info = self.bql_util.batch_exec_reqs(self.tuple_trend_reqs,combine_resulting_dfs=False)

        except:
            self.log_message('Error running BQL queries for trend data.')
            first_query_str = self.tuple_trend_reqs[0][1].to_string()
            self.log_message('First BQL Query: {}'.format(first_query_str),color='red')
            return None
        self.log_message('Completed {} BQL queries getting trend data'.format(len(self.l_df)),preserve_spinner=True)

        ##construct df_oas and df_ytw

        # l_ser_oas = list()
        # l_ser_ytw = list()
        l_ser_metric = list()
        for i in range(len(self.l_df)):
            resp = self.l_df[i]
            #resp is parallel to l_metric_info
            dict_dicts=dict()
            dict_dicts[metric_str]=dict()
            # dict_dicts['OAS']=dict()
            # dict_dicts['YTW']=dict()

            for j in range(len(resp)):
                elt = self.l_df[i][j]
                info = self.l_dict_info[i]
                metric_info=self.bql_util.l_metric_info[j]
                df = elt.df()
                dt_val = df['DATE'].iloc[0]
                val = df[df.columns[-1]].iloc[0]    
                metric_label = metric_info['label']
                dict_dicts[metric_label][dt_val] = val
            
            #construct series, and append to series list
            ser_metric = pd.Series(dict_dicts[metric_str],name=info['Label'])
            l_ser_metric.append(ser_metric)

            # ser_oas = pd.Series(dict_dicts['OAS'],name=info['Label'])
            # l_ser_oas.append(ser_oas)
            
            # ser_ytw = pd.Series(dict_dicts['YTW'],name=info['Label'])
            # l_ser_ytw.append(ser_ytw)    
                
        # df_oas = pd.DataFrame(l_ser_oas).transpose()
        # df_ytw = pd.DataFrame(l_ser_ytw).transpose()
        df_metric = pd.DataFrame(l_ser_metric).transpose()
        

        trend_data = collections.OrderedDict()
        # trend_data['OAS']=df_oas
        # trend_data['YTW']=df_ytw
        trend_data[metric_str]=df_metric

        self.dict_data['trend_data']=trend_data

        return trend_data



    def _get_oas_ytw_data(self,ticker, start_univ_override_str=None, seniority_str=None, metric_str=None, ccy_str=None):
        """
        Summary: Constructs data for input ticker
        Input: ticker String
        Output: Dictionary with keys 'OAS' and 'YTW', with the value of a dataframe of "response" data. 
            Each DataFrame has index of the Maturity Buckets (e.g. <1yr, 2yr,3yr,...) and has a column for each Universe (e.g. UTX Bonds, All BBB Rated, )

        """
        df_top_level_summary = self.dict_data['top_level_summary_data']
        country = df_top_level_summary.loc['Country'].iloc[0]
        sp_rating = df_top_level_summary.loc['S&P Rating'].iloc[0]

        if sp_rating is None:
            company_name = df_top_level_summary.loc['Name'][0]
            self.log_message('{} does not have a S&P Rating. Skipping OAS_YTW retrieval'.format(company_name),preserve_spinner=True)
            return None
        rating_bucket = self.df_config_rtg_buckets[self.df_config_rtg_buckets['sp_rtg']==sp_rating]['bucket'].iloc[0]
        sector = df_top_level_summary.loc['BICS Level 1 Sector'].iloc[0]
        industry_group = df_top_level_summary.loc['BICS Level 2 Industry Group'].iloc[0]

        # oas_def = {'Name':'OAS','Label':'OAS','bql_str':"bq.data.spread(spread_type='oas')['value']"}
        # ytw_def = {'Name':'YTW','Label':'YTW','bql_str':"bq.data.yield_(yield_type='ytw')['value']"} 


        # ###TODO: look up the metric based on the metric_str

        # if metric_str=='OAS':
        #     l_metrics=[oas_def]
        # elif metric_str=='YTW':
        #     l_metrics=[ytw_def]
        # else: 
        #     l_metrics=[oas_def]

        bql_str = self.lookup_bql_str_for_metric(metric_str)
        metric_def = {'Name':metric_str, 'Label':metric_str, 'bql_str':bql_str}
        l_metrics = [metric_def]



        self.tuples_reqs_with_info=self.bql_util.construct_aggregated_oas_ytw_data_requests(ticker=ticker, country_iso=country, rating_bucket=rating_bucket, sector=sector, industry_group=industry_group, l_metrics=l_metrics, base_univ_start=start_univ_override_str, seniority_str=seniority_str, ccy_str=ccy_str)

        ##next need to execute asynchronously the requests in list. 
        od_univs = collections.OrderedDict()
        od_flds = collections.OrderedDict()
        for elt in self.tuples_reqs_with_info:
            elt_info=elt[0]
            for metric_name in elt_info['Metric Names']:
                od_flds[metric_name]=1
            od_univs[elt_info['Universe Label']]=1
        str_unique_univs = str(list(od_univs.keys()))
        str_unique_fields = str(list(od_flds.keys()))


        self.log_message('Querying BQL with {} total requests, for {} metrics: {}, and for universes: {}'.format(len(self.tuples_reqs_with_info),len(od_flds.keys()),str_unique_fields, str_unique_univs),preserve_spinner=True)

        if self.bql_util.is_bql_verbose:
            for tup in self.tuples_reqs_with_info:
                dict_info=tup[0]
                req=tup[1]
                str_info = "Querying Universe: {}".format(dict_info['Universe Label'])
                self.log_message(str_info, color='yellow',preserve_spinner=True)
                self.log_message(req.to_string(), preserve_spinner=True)

        try:
            self.l_df, self.l_dict_info = self.bql_util.batch_exec_reqs(self.tuples_reqs_with_info,execute_asynchronously=True)
        except:
            self.log_message('Error running BQL queries on {}, on universes: {}'.format(str_unique_fields, str_unique_univs))
            first_query_str = self.tuples_reqs_with_info[0][1].to_string()
            self.log_message('First BQL Query: {}'.format(first_query_str),color='red')
            return None
        self.log_message('Completed {} BQL queries getting OAS and YTW data'.format(len(self.l_df)),preserve_spinner=True)

        #put univ_labels into dict_univ_labels
        univ_label_tups = [(x[0]['Universe Name'],x[0]['Universe Label']) for x in self.tuples_reqs_with_info]
        dict_univ_labels = dict()
        for tup in univ_label_tups:
            dict_univ_labels[tup[1]] = tup[0]
        # dict_univ_labels        


        ##l_df is a parallel list to l_dict_info
        ## each element in l_df is a dataframe corresponds to a bql response object
        ## each element in l_dict_info is a dictionary with info about the query
        ##organize l_df data into dictionary: field -> dataframe

        ##Iterate through responses for Maturity Buckets
        l_tups = [x for x in self.l_dict_info if x['Bucket Name']=='Maturity Bucket']      
        self.d_fld_to_df=dict()
        if len(l_tups)<0:
            self.log_message('No data retrieved for OAS and YTW')
            return None
        for metric_name in l_tups[0]['Metric Names']:
            self.d_fld_to_df[metric_name]=pd.DataFrame()
        
        for i in range(len(l_tups)):
            dict_info = l_tups[i]
            for metric_name in dict_info['Metric Names']:
                col_data = self.l_df[i][metric_name]
                label_intersection = list(set(col_data.index) & set(self.df_config_mat_buckets.label))
                sorted_label_intersection = sorted(label_intersection, key=lambda x: self.df_config_mat_buckets.label.tolist().index(x))
                col_ordered = col_data.loc[sorted_label_intersection]
                self.d_fld_to_df[metric_name][dict_info['Universe Label']] = col_ordered        


        fld_names = [x['Name'] for x in l_metrics]
        ##Next Iterate through responses for All Maturity Buckets Aggregated together
        for fld_name in fld_names:
            #for each field
            #construct newser to append        
            dict_newser_to_append=dict()
            
            for zipped_tup in zip(self.l_dict_info,self.l_df):
                #go through only the "All Maturites" hits
                dict_info = zipped_tup[0]    
                bucket_name = dict_info['Bucket Name']
                if bucket_name=='All Maturities':
                    df_oas_ytw = zipped_tup[1]
                    univ_name = dict_info['Universe Name']
                    univ_label = dict_info['Universe Label']
                    
                    val = df_oas_ytw[fld_name].iloc[0]
                    dict_newser_to_append[univ_label] = val
                
            newser = pd.Series(dict_newser_to_append,name='All')    
            self.d_fld_to_df[fld_name] = self.d_fld_to_df[fld_name].append(newser)



        return self.d_fld_to_df, dict_univ_labels
        

    def do_analyze(self, ticker ,start_univ_override_str=None, seniority_str=None, metric_str=None, ccy_str=None):

        #clear dict_data and display
        self.dict_data=collections.OrderedDict()
        self.ui.redraw_gui(force_clear=True)

        ##put spinner box in each tab
        self.ui.top_level_summary_area.children=[self.ui.spinner_box]
        self.ui.term_structure_area.children = [self.ui.spinner_box]
        self.ui.fundamental_area.children = [self.ui.spinner_box]


        ##validate ticker
        if not self.bql_util._ticker_is_valid(ticker):
            self.log_message("Ticker '{}' is not formatted properly".format(ticker),color='yellow')
            return

        self.ui.drilldown_ticker_element.value=ticker


        #populate dict_data
        self.log_message('Retrieving top level summary data for {}'.format(ticker), preserve_spinner=True)
        
        # try:
        top_level_summary_data = self._get_top_level_summary_data(ticker)
        self.dict_data['top_level_summary_data']=top_level_summary_data
        # except Exception as exc:
        #     self.log_message('Eror retrieving top level summary data: {}'.format('<br>'.join(traceback.format_exc().splitlines())),color='Yellow')

        self.ui.redraw_gui(['top_level_summary'])

        self.log_message('Retrieving OAS and YTW for table for {}'.format(ticker), preserve_spinner=True)
        self.dict_data['oas_ytw_data'], self.dict_data['univ_labels']=self._get_oas_ytw_data(ticker, start_univ_override_str, seniority_str, metric_str, ccy_str)
        self.ui.redraw_gui(['term_structure'])

        self.log_message('Retrieving Fundamental data for peer companies', preserve_spinner=True)
        self.dict_data['fundamental_data']=self._get_fundamentals_for_peers(ticker)
        self.ui.redraw_gui(['fundamental'])

        self.ui.redraw_gui(['trends'])

        self.log_message('Completed retrieval for {}'.format(ticker),spinner=False)

        #send dict_data to ui

    def _strip_ticker(self, ticker):
        if ticker.endswith(' Equity'):
            ticker = ticker[0:-7]
        if len(ticker) < 4:
            return ticker
        if ticker[-3:-1]==' U':
            return ticker[0:-3]
        else:
            return ticker            

    def log_message(self, message, color=None, spinner=False, preserve_spinner=False):
        try:
            self.ui
        except:
            ### No ui available yet for logging.
            return
        self.ui.update_status(message, color=color, spinner=spinner, preserve_spinner=preserve_spinner)     


    def show(self):
        ui = self.ui
        return ui.show()