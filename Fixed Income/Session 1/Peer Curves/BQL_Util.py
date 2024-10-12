import bql
import collections
import pandas as pd
class BQL_Util():
    def __init__(self, bq=None, app=None):
        """
        instantiate bq Service object
        """
        if bq is not None:
            self.bq = bq
        else:
            self.bq = bql.Service()        
        self.app = app
        self.is_bql_verbose=False

    def _refresh_bql_service(self):
        self.bq = bql.Service()


    def get_return_series(self, univ, start_dt_str, end_dt_str, per='M'):
        """
        Utility function to retrieve monthly return series between specified start and end times.         
        Returns data frame indexed by "YYYYMM"
        """
        bq = self.bq
        flds = bq.data.return_series(calc_interval=bq.func.range(start_dt_str,end_dt_str), per=per)
        req = bql.Request(universe=univ, items=flds)
        resp = bq.execute(req)

        df_ftw = resp[0].df().reset_index().pivot(index='DATE',columns='ID',values=resp[0].df().columns[-1])
        df_ftw.index = df_ftw.index.strftime('%Y%m')
        df_ftw.index.name = 'YYYYMM'
        df_ftw = df_ftw[univ]
        return df_ftw

    def get_px_last(self, univ, start_dt_str, end_dt_str, per='M'):
        """
        Utility function to retrieve monthly prices from BQL
        """
        bq = self.bq
        flds = bq.data.px_last(dates=bq.func.range(start_dt_str,end_dt_str), per=per, fill='prev')
        req = bql.Request(universe=univ, items=flds)
        resp = bq.execute(req)

        df = resp[0].df().reset_index().pivot(index='DATE',columns='ID',values=resp[0].df().columns[-1])
        df.index = df.index.strftime('%Y%m')
        df.index.name = 'YYYYMM'
        return df

    def validate_top_level_summary_code(self):
        bq = self.bq
        df_cfg = self.app.df_config_top_level_summary

        l_bql_expr=[]
        for i in range(len(df_cfg.index)):
            s_row = df_cfg.iloc[i]
            field = s_row['Field']
            bql_str = s_row['BQL Code']
            try:
                bql_expr = eval(bql_str)
                l_bql_expr.append(bql_expr)
            except:
                self.app.log_message('Warning! Unable to validate top level summary BQL query for {}:{}'.format(field,bql_str))
                return

        self.app.df_config_top_level_summary = self.app.df_config_top_level_summary.assign(bql_expr=l_bql_expr)
        # self.app.log_message('Validated proper formulation of top level summary BQL queries')


    def retrieve_top_level_summary_data(self, ticker):
        """
        Function to retrieve the top level summary data for an input ticker
        """

        bq = self.bq
        flds = collections.OrderedDict()

        #get config data for 
        df_cfg_top_level = self.app.df_config_top_level_summary
        # df_cfg_fundamentals = self.app.df_config_fundamentals

        for i in range(len(df_cfg_top_level.index)):
            s_row = df_cfg_top_level.iloc[i]
            field = s_row['Field']
            bql_str = s_row['BQL Code']
            bql_expr = s_row['bql_expr']
            flds[field] = bql_expr

        req = bql.Request(universe=ticker,items=flds)

        df = self.execute_bql_query(req)

        if df is None:
            return df
        return df.transpose()

    def _ticker_is_valid(self, ticker):
        bq = self.bq
        try:
            flds = {'ticker':bq.data.ticker()}
            req = bql.Request(universe=ticker, items=flds)
            resp = bq.execute(req)
            df = resp[0].df()
            s = df.iloc[0]['ticker']
            if s is None or s=='':
                return False
            else:
                return True
        except:
            return False

    def __drilldown_construct_univ(self, ticker, mat_str, univ_str, univ_selector_str,index_str,seniority_str, country, rating_bucket,sector,industry_group, ccy_str, max_num_results=100, min_amt_outstanding_usd=25000000):
        bq = self.bq       

        mat_bucket_bql_expr = self._construct_mat_bucket_bql_def(self.app.df_config_mat_buckets)
        rtg_bucket_bql_expr = self._construct_rtg_bucket_bql_def(self._collapse_df_rtgs(self.app.df_config_rtg_buckets))          

        base_univ_start = None
        if univ_selector_str=='Index':
            base_univ_start = bq.univ.members(index_str)
        else:
            base_univ_start = None        
        base_univ = self.__get_default_base_univ(min_amt_outstanding_usd, country, base_univ_start, seniority_str, ccy_str)

        ##Filter base_univ according to Universe Selection
        if univ_str=='Ticker Only':

            ticker_base_univ = self.__get_default_base_univ(min_amt_outstanding_usd=min_amt_outstanding_usd, country_iso=country, base_univ_start=bq.univ.bonds(ticker), seniority_str=seniority_str, ccy_str=ccy_str)
            base_univ = bq.univ.filter(ticker_base_univ, bq.func.grouprank(bq.data.amt_outstanding(currency='USD'))<=max_num_results)

            if mat_str != 'All Maturities':
                base_univ = bq.univ.filter(base_univ, mat_bucket_bql_expr==mat_str)

        elif univ_str=='Rating Bucket':
            # print('filter by rating bucket')
            base_univ = bq.univ.filter(base_univ, rtg_bucket_bql_expr==rating_bucket) 
        elif univ_str=='Sector':
            # print('filter by sector bucket')
            base_univ = bq.univ.filter(base_univ, bq.data.classification_name('BICS','1')==sector)
        elif univ_str=='Industry Group':
            # print('filter by industry group')
            base_univ = bq.univ.filter(base_univ, bq.data.classification_name('BICS','2')==industry_group)
        elif univ_str=='Rating & Sector':
            # print('filter by rating and sector')
            base_univ = bq.univ.filter(base_univ, rtg_bucket_bql_expr==rating_bucket) 
            base_univ = bq.univ.filter(base_univ, bq.data.classification_name('BICS','1')==sector)
        else:
            # print('filter by Rating and industry group. univ_str:{}'.format(univ_str))
            base_univ = bq.univ.filter(base_univ, rtg_bucket_bql_expr==rating_bucket) 
            base_univ = bq.univ.filter(base_univ, bq.data.classification_name('BICS','2')==industry_group)


        ##Filter base_univ according to Maturity Bucket
        if mat_str != 'All Maturities':
            base_univ = bq.univ.filter(base_univ, mat_bucket_bql_expr==mat_str)

        ##Filter based on max number of results
        filt_univ = bq.univ.filter(base_univ, bq.func.grouprank(bq.data.amt_outstanding(currency='USD'))<=max_num_results)

        return filt_univ


    def __drilldown_construct_flds(self):
        bq = self.bq
        flds = collections.OrderedDict()
        flds['Name']=bq.data.name()
        flds['Ticker']=bq.data.ticker()

        ##put all metrics in to flds dictionary
        l_metric_names = self.app.get_list_of_metric_names()
        for metric_name in l_metric_names:
            bql_str = self.app.lookup_bql_str_for_metric(metric_name)
            bql_elt = eval(bql_str)
            flds[metric_name] = bql_elt

        # flds['OAS']=bq.data.spread(spread_type='oas')['value']
        # flds['YTW']=bq.data.yield_(yield_type='ytw')['value']
        # flds['Z Spread']=bq.data.spread(spread_type='Z')['value']
        flds['Years to mat']=(bq.data.maturity()-bq.func.today())/365        
        flds['Amt Out (M)']=bq.data.amt_outstanding(currency='USD')['value']/1000000
        flds['Currency']=bq.data.crncy()
        flds['Coupon Type']=bq.data.cpn_typ()
        flds['Payment Rank']=bq.data.payment_rank()

        return flds

    def query_drilldown(self, ticker, mat_str, univ_str, univ_selector_str,index_str,seniority_str, country, rating_bucket,sector,industry_group, ccy_str,max_num_results=100):
        bq = self.bq


        #construct universe
        univ = self.__drilldown_construct_univ(ticker, mat_str, univ_str, univ_selector_str,index_str,seniority_str, country, rating_bucket,sector,industry_group, ccy_str, max_num_results=max_num_results)

        #construct fields
        flds = self.__drilldown_construct_flds()


        req = bql.Request(universe=univ, items=flds)
        
        # print(req.to_string())

        df_resp = self.execute_bql_query(req)

        return df_resp
        # return None


    def retrieve_fundamental_data(self, ticker, country, min_mkt_cap_b, max_mkt_cap_b, gics_subindustry, gics_sector):
        bq = self.bq
        ##contruct universe
        starting_univ = bq.univ.equitiesuniv(['active','primary'])
        #filter by country
        base_univ = bq.univ.filter(starting_univ,bq.data.country_iso()==country)
        #filter by gics_subindustry
        base_univ = bq.univ.filter(base_univ,bq.data.gics_sub_industry_name()==gics_subindustry)
        #filter by market cap
        if max_mkt_cap_b is None:
            base_univ = bq.univ.filter(base_univ,bq.data.cur_mkt_cap(currency='USD')/1000000>=min_mkt_cap_b*1000)
        else:
            base_univ = bq.univ.filter(base_univ,bq.func.and_(bq.data.cur_mkt_cap(currency='USD')/1000000>=min_mkt_cap_b*1000,
                                                              bq.data.cur_mkt_cap(currency='USD')/1000000<=max_mkt_cap_b*1000))

        if gics_sector=='Financials':
            df_config_fundamentals = self.app.df_config_fundamentals_financials
        else:
            df_config_fundamentals = self.app.df_config_fundamentals
        ##construct bql expressions for the bql_string inputs
        exprs = list()
        for s in df_config_fundamentals['bql_string']:
            exprs.append(eval(s))
        df_config_fundamentals['bql_expr']=exprs


        #construct fields dictionary
        flds = collections.OrderedDict()

        for i in range(len(df_config_fundamentals.index)):
            field_label=df_config_fundamentals.iloc[i]['field_label']
            bql_expr = df_config_fundamentals.iloc[i]['bql_expr']
            flds[field_label]=bql_expr

        req = bql.Request(universe=base_univ, items=flds)
        df = self.execute_bql_query(req)

        ##order the results -- put ticker at the top 
        df1 = df.loc[[ticker]]
        df2 = df[~df.index.isin([ticker])]
        df = df1.append(df2)

        ##put the nearest companies by market cap up top
        this_mkt_cap = df.iloc[0]['Market Cap (B)']
        # df2 = df.assign(diff_to_mkt_cap = (df['Market Cap (B)']-this_mkt_cap).abs())
        # df_sorted = df2.sort_values('diff_to_mkt_cap').drop('diff_to_mkt_cap',axis=1)
        df_sorted = df.sort_values('Market Cap (B)',ascending=False)

        return df_sorted




    def _construct_mat_bucket_bql_def(self, df_cfg):
        bq = self.bq
        mat_yrs = (bq.data.maturity()-bq.func.today())/365

        if len(df_cfg.index)==0:
            return 'other'
        df_new = df_cfg.iloc[1:]
        return(bq.func.if_(bq.func.and_(mat_yrs>df_cfg.iloc[0]['low_limit'],mat_yrs<=df_cfg.iloc[0]['high_limit']),df_cfg.iloc[0]['label'],self._construct_mat_bucket_bql_def(df_new)))


    def _construct_rtg_bucket_bql_def(self, df_cfg):
        bq = self.bq

        rtg = bq.data.rating(rating_source='SP')['value']

        if len(df_cfg.index)==0:
            return 'unrated'
        df_new = df_cfg.iloc[1:]
        return bq.func.if_(bq.func.in_(rtg,df_cfg.iloc[0]['list']),df_cfg.iloc[0]['bucket'],self._construct_rtg_bucket_bql_def(df_new))

        
    def _collapse_df_rtgs(self, df_rtg):
        df_collapsed = pd.DataFrame()
        l_buckets = df_rtg['bucket'].unique().tolist()
        for b in l_buckets:
            df_sub = df_rtg[df_rtg['bucket']==b]
            l_rtgs = df_sub['sp_rtg'].tolist()
            dict_new = collections.OrderedDict()
            dict_new['list']=l_rtgs
            dict_new['bucket']=b
            ser = pd.Series(dict_new)
            df_collapsed = df_collapsed.append(ser,ignore_index=True)
        return df_collapsed

    def construct_trend_oas_ytw_requests(self, mat_bucket_str, ticker, country_iso, rating_bucket, sector, industry_group, metric_info, base_univ_start=None, min_amt_outstanding_usd=25000000, seniority_str=None, ccy_str=None):
        bq = self.bq

        mat_bucket_bql_expr = self._construct_mat_bucket_bql_def(self.app.df_config_mat_buckets)
        all_buckets_bql_expr= None

        rtg_bucket_bql_expr = self._construct_rtg_bucket_bql_def(self._collapse_df_rtgs(self.app.df_config_rtg_buckets))

        ##populate input variables
        aggregation_function = bq.func.avg   

        base_univ = self.__get_default_base_univ(min_amt_outstanding_usd=min_amt_outstanding_usd, country_iso=country_iso, base_univ_start=base_univ_start, seniority_str=seniority_str, ccy_str=ccy_str)
        #ticker_base_univ = self.__get_default_base_univ(min_amt_outstanding_usd=min_amt_outstanding_usd, country_iso=country_iso, base_univ_start=bq.univ.bonds(ticker), seniority_str=seniority_str, ccy_str=ccy_str)        
        ticker_base_univ = self.__get_default_base_univ(min_amt_outstanding_usd=min_amt_outstanding_usd, country_iso=country_iso, base_univ_start=bq.univ.bonds(ticker,issuedby='credit_family'), seniority_str=seniority_str, ccy_str=ccy_str)        

        ##filter universe based on input maturity bucket
        if mat_bucket_str=='All Maturities':
            filtered_univ = base_univ
            filtered_ticker_univ = ticker_base_univ
        else:
            filtered_univ = bq.univ.filter(base_univ,mat_bucket_bql_expr==mat_bucket_str)
            filtered_ticker_univ = bq.univ.filter(ticker_base_univ,mat_bucket_bql_expr==mat_bucket_str)

        # l_buckets = self.__get_default_l_buckets()
        l_univ_dicts = self.__get_default_l_univ_dicts(filtered_univ, rtg_bucket_bql_expr, ticker, rating_bucket, sector, industry_group, filtered_ticker_univ)




        ##construct metrics to query
        self.l_metric_info=list()

        metric_label = metric_info['Name']
        l_tups = metric_info['tups']

        for tup in l_tups:
            date_str = tup[0]
            bql_expr = tup[1]
            ##append data to l_metric_info
            metric_info=dict()
            metric_info['label']=metric_label
            metric_info['as_of_date']=date_str
            metric_info['bql_str']=bql_expr
            metric_info['bql_expr']=eval(bql_expr)
            metric_info['bql_return_label']='{}_{}'.format(metric_label,date_str)
            self.l_metric_info.append(metric_info)
        # constuct fields dictionary 

        flds = collections.OrderedDict()
        for d in self.l_metric_info:
            flds[d['bql_return_label']]=d['bql_expr']


        ##construct BQL requests
        l_bql_req_tups = list()        

        for univ_dict in l_univ_dicts:            
            univ = univ_dict['bql_expr']            
            bql_req = bql.Request(universe=univ, items=flds)            
            bql_dict_info = dict()
            bql_dict_info['Label']=univ_dict['Label']
            bql_dict_info['Name']=univ_dict['Name']
            tup = (bql_dict_info, bql_req)
            l_bql_req_tups.append(tup)

        return l_bql_req_tups

        # tmp_return_dict = {'base_univ':base_univ, 'l_metric_info':l_metric_info, 'l_univ_dicts':l_univ_dicts,'flds':flds,'l_bql_req_tups':l_bql_req_tups}
        # return tmp_return_dict


    def __get_default_base_univ(self, min_amt_outstanding_usd, country_iso, base_univ_start, seniority_str, ccy_str):
        bq=self.bq
        if base_univ_start is None:
            base_univ_start=bq.univ.bondsuniv('active')
        elif type(base_univ_start)==str:
            base_univ_start = eval("bq.univ.members('{}')".format(base_univ_start))
        if seniority_str is None:
            pass
        elif seniority_str=='Senior':
            base_univ_start = bq.univ.filter(base_univ_start,bq.func.in_(bq.data.payment_rank(),self.app.SENIOR_STR_LIST))
        elif seniority_str=='Sub':
            base_univ_start = bq.univ.filter(base_univ_start,bq.func.in_(bq.data.payment_rank(),self.app.SUB_STR_LIST))

        if ccy_str is not None:
            base_univ_start = bq.univ.filter(base_univ_start,bq.data.crncy()==ccy_str)

        base_univ = bq.univ.filter(bq.univ.filter(base_univ_start,bq.data.amt_outstanding(currency='USD')>=min_amt_outstanding_usd),bq.data.country_iso()==country_iso)
        return base_univ

    def __get_default_l_buckets(self):
        bq = self.bq
        mat_bucket_dict={'Name':'Maturity Bucket','Label':'Maturity Bucket','bql_str':'mat_bucket_bql_expr'}
        all_maturities_dict={'Name':'All Maturities','Label':'All','bql_str':'all_buckets_bql_expr'}
        l_buckets=[mat_bucket_dict, all_maturities_dict]
        return l_buckets

    def __get_default_l_univ_dicts(self, base_univ, rtg_bucket_bql_expr, ticker, rating_bucket, sector, industry_group, ticker_base_univ):        
        bq = self.bq
        l_univ_dicts=[]
        # ticker_univ_dict={'Name':'Ticker', 'Label':'{} Bonds'.format(self.app._strip_ticker(ticker)),'bql_str':"bq.univ.bonds('{}')".format(ticker)}
        ticker_univ_dict={'Name':'Ticker', 'Label':'{} Bonds'.format(self.app._strip_ticker(ticker)),'bql_expr':ticker_base_univ}
        
        l_univ_dicts.append(ticker_univ_dict)
        rtg_univ_dict={'Name':'Rating','Label':'All {} Rated'.format(rating_bucket), 'bql_str':"bq.univ.filter(base_univ,rtg_bucket_bql_expr=='{}')".format(rating_bucket)}
        l_univ_dicts.append(rtg_univ_dict)
        sector_univ_dict={'Name':'Sector','Label':'{}'.format(sector), 'bql_str':"bq.univ.filter(base_univ,bq.data.classification_name('BICS','1')=='{}')".format(sector)}
        l_univ_dicts.append(sector_univ_dict)            
        industry_univ_dict={'Name':'Industry Group','Label':'{}'.format(industry_group), 'bql_str':"bq.univ.filter(base_univ,bq.data.classification_name('BICS','2')=='{}')".format(industry_group)}
        l_univ_dicts.append(industry_univ_dict)
        sector_and_rtg_univ_dict={'Name':'Sector & Rating','Label':'{} and {}'.format(rating_bucket,sector), 'bql_str':"bq.univ.filter(bq.univ.filter(base_univ,bq.data.classification_name('BICS','1')=='{}'),rtg_bucket_bql_expr=='{}')".format(sector,rating_bucket)}            
        l_univ_dicts.append(sector_and_rtg_univ_dict)
        industry_and_rtg_univ_dict={'Name':'Industry & Rating','Label':'{} and {}'.format(rating_bucket,industry_group), 'bql_str':"bq.univ.filter(bq.univ.filter(base_univ,bq.data.classification_name('BICS','2')=='{}'),rtg_bucket_bql_expr=='{}')".format(industry_group,rating_bucket)}            
        l_univ_dicts.append(industry_and_rtg_univ_dict)   

        for univ_dict in l_univ_dicts:
            if 'bql_expr' not in univ_dict.keys():
                univ_dict['bql_expr']=eval(univ_dict['bql_str'])    

        return l_univ_dicts        


    
        

    def construct_aggregated_oas_ytw_data_requests(self, ticker, country_iso, rating_bucket, sector, industry_group, aggregation_function=None, l_metrics=None, base_univ_start=None, seniority_str=None, ccy_str=None, min_amt_outstanding_usd=25000000):
        bq = self.bq

        #instantiate variables
        mat_bucket_bql_expr = self._construct_mat_bucket_bql_def(self.app.df_config_mat_buckets)
        # mat_bucket_dict= {'Name':'Maturity Bucket',
        #                   'Label':'Maturity Bucket',
        #                   'bql_expr':mat_bucket_bql_expr}
        all_buckets_bql_expr= None


        rtg_bucket_bql_expr = self._construct_rtg_bucket_bql_def(self._collapse_df_rtgs(self.app.df_config_rtg_buckets))

        ##populate input variables
        if aggregation_function is None:
            aggregation_function = bq.func.avg    

        base_univ = self.__get_default_base_univ(min_amt_outstanding_usd, country_iso, base_univ_start, seniority_str, ccy_str)
        #ticker_base_univ = self.__get_default_base_univ(min_amt_outstanding_usd=min_amt_outstanding_usd, country_iso=country_iso, base_univ_start=bq.univ.bonds(ticker), seniority_str=seniority_str, ccy_str=ccy_str)
        ticker_base_univ = self.__get_default_base_univ(min_amt_outstanding_usd=min_amt_outstanding_usd, country_iso=country_iso, base_univ_start=bq.univ.bonds(ticker,issuedby='credit_family'), seniority_str=seniority_str, ccy_str=ccy_str)

        l_buckets = self.__get_default_l_buckets()
        for bucket_dict in l_buckets:
            bucket_dict['bql_expr']=eval(bucket_dict['bql_str'])
        l_univ_dicts = self.__get_default_l_univ_dicts(base_univ, rtg_bucket_bql_expr, ticker, rating_bucket, sector, industry_group, ticker_base_univ)

        if l_metrics is None:
            oas_def = {'Name':'OAS','Label':'OAS','bql_str':"bq.data.spread(spread_type='oas')['value']"}
            ytw_def = {'Name':'YTW','Label':'YTW','bql_str':"bq.data.yield_(yield_type='ytw')['value']"} 
            l_metrics=[oas_def,ytw_def]
        for metric_dict in l_metrics:
            metric_dict['bql_expr']=eval(metric_dict['bql_str'])


            ######
            ####need also to append sector, industry, rating & sector, rating&industry


        # for i in range(len(l_univ_dicts)):

            # print('l_univ_dicts[{}]:\n{}'.format(i,l_univ_dicts[i]))

        
        #populate bql_requests
        l_req_info=list()
        l_reqs=list()
        for bucket in l_buckets:
            bucket_name=bucket['Name']
            bucket_label=bucket['Label']
            for univ_dict in l_univ_dicts:
                univ_name=univ_dict['Name']
                univ_label=univ_dict['Label']
                fld_dict = collections.OrderedDict()
                l_metric_names=list()
                l_metric_labels=list()
                for metric in l_metrics:
                    metric_name=metric['Name']
                    l_metric_names.append(metric_name)
                    metric_label=metric['Label']
                    l_metric_labels.append(metric_label)
                    if bucket['bql_expr'] is None:
                        fld_dict[metric_name] = aggregation_function(bq.func.group(metric['bql_expr']))['value']
                    else:    
                        fld_dict[metric_name] = aggregation_function(bq.func.group(metric['bql_expr'],bucket['bql_expr']))['value']

                # print('len(fld_dict):\n{}'.format(len(fld_dict)))    


                dict_req_info={'Bucket Name':bucket_name,'Bucket Label':bucket_label,'Universe Name':univ_name,'Universe Label':univ_label,'Metric Names':l_metric_names,'Metric Labels':l_metric_labels}
                l_req_info.append(dict_req_info)
                req = bql.Request(universe=univ_dict['bql_expr'],items=fld_dict)
                # print('Request:\n {}'.format(req.to_string()))
                l_reqs.append(req)        

        #construct tuples
        l_tuples = list()
        for i in range(len(l_reqs)):
            tup = l_req_info[i],l_reqs[i]
            l_tuples.append(tup)

        return l_tuples




    def batch_exec_reqs(self, l_tuples, execute_asynchronously=True, combine_resulting_dfs=True):

        """
        Summary: Utility to execute BQL requests asynchronously.
        Input: list of tuples, wherein...
            Element 0 is a dictionary of information about the request. 
            Element 1 is a BQL request object
        Output: 2 items: 
                a list of data frame corresponding to Non-Erroring of each BQL Request
                a list of dictionary of request info

        """
        bq = self.bq
        
        l_req_info = [x[0] for x in l_tuples]
        l_reqs = [x[1] for x in l_tuples]

    
        #construct result promises for each bql query
        # print('Preparing to execute BQL requests asynchronously for {} individual requests'.format(len(l_reqs)))

        result_promises = [bq.execute(req, lambda resp: resp) for req in l_reqs]  

        
        # print("Requesting batch of BQL queries for {} requests:\n{}".format(len(l_req_info),l_req_info))
        # print('First query, for details {}, is:\n{}'.format(str(l_req_info[0]),l_reqs[0].to_string()))

        ## execute requests asynchronously
        # self.l_orig_responses=list()
        responses =[]
        l_info = []
        for i in range(len(result_promises)):
            try:
                p=result_promises[i]
                req_info = l_req_info[i]
                response = p.result()
                # self.l_orig_responses.append(response)
                if combine_resulting_dfs:
                    df = bql.combined_df(response)
                    responses.append(df)
                else:
                    responses.append(response)
                l_info.append(req_info)
            except:
                req_info = l_req_info[i]
                universe_str = ''
                if 'Universe Label' in req_info.keys():
                    universe_str = req_info['Universe Label']
                elif 'Label' in req_info.keys():
                    universe_str = req_info['Label']
                metric_str = ''
                if 'Metric Names' in req_info.keys():
                    metric_str = req_info['Metric Names']
                bucket_str = ''
                if 'Bucket Label' in req_info.keys():
                    bucket_str = req_info['Bucket Label']

                the_message = 'BQL Error, querying Universe: {}'.format(universe_str)
                if len(metric_str) >0:
                    the_message = the_message + 'Metric: {}'.format(metric_str)
                if len(bucket_str) > 0:
                    the_message = the_message + 'Bucket: {}'.format(bucket_str)

                self.app.log_message(the_message,preserve_spinner=True)
                # self.app.log_message('{}'.format(l_reqs[i].to_string()),preserve_spinner=True)


        # responses = [p.result() for p in result_promises]

        #construct list of result data frames
        # l_df = [x[0].df() for x in responses]
        # l_df = [bql.combined_df(x) for x in responses]

        
        return responses, l_info



    
    
    def execute_bql_query(self, bql_request):
        bq = self.bq
        try:
            resp = bq.execute(bql_request)
            df_resp = bql.combined_df(resp)
            return df_resp
        except:
            self.app.log_message('Error Executing BQL Query: {}'.format(bql_request.to_string()),color='red',preserve_spinner=True)
            return None        
