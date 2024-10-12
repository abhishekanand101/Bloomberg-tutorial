cimport bql
from collections import OrderedDict
import pandas as pd
import logging
import constants
from itertools import chain
import numpy as np


_LOGGER = logging.getLogger('CreditApp')


class DataModel():
    """
    Model for requesting data and building screening and scoring
    """

    # BQL Service instance shared across FactorModel instances.
    __shared_bq__ = None

    def __init__(self, ticker, lookback_period, periodicity, sprd_level, sprd_side, config, ptf_only, bq=None):
        """
        Initialize model.
        Parameters
        start_date (date): start date of holdings
        end_date (date): end date of holdings
        bq (bql.Service): Instance of bql Service.
                          It would lazily create BQL service instance only when requesting for data.
                          If an instance is provided through bq parameter,
                          this instance would be used.
        """
        self._bq = bq
        self.lookback = abs(lookback_period)
        self.periodicity = periodicity
        self.sprd_level = sprd_level
        self.sprd_side = sprd_side
        self.ticker = ticker
        self.univ = None
        self.preferences = {'unitscheck': 'ignore'}
        self.data = None
        self.data_heatmap = None
        self.data_ptf = None
        self.ptf_only = ptf_only
        self.sprd_type = 'OAS'
        my_config = pd.read_csv("config.csv", index_col='Field Name')
        my_config.update(config)
        self.config = my_config

    def _init_bql(self):
        """Loads self._bq from class-level shared BQL instance if no instance is available yet.
        Class-level shared BQL instance would be initialized if needed.
        """
        if self._bq is None:
            if DataModel.__shared_bq__ is None:
                _LOGGER.info('Launching BQL service...')
                DataModel.__shared_bq__ = bql.Service()
                _LOGGER.info('BQL service up and running...')
            self._bq = DataModel.__shared_bq__

    def run(self):
        """ Runs the main code to retrieve and manipulate data
        """
        try:
            self._init_bql()
            self.data = self.get_results_screening()
        except Exception as e:
            _LOGGER.error('Error retrieving screening data ... %s', e)

    def run_heatmap(self, heatmap_toggle):
        """ Get the data for the heatmap for the spread analysis
        """
        try:
            self._init_bql()
            self.data_heatmap = self.get_heatmap_formatted_data(heatmap_toggle)
        except Exception as e:
            _LOGGER.error('Error retrieving heatmap data ... %s', e)

    def get_current_fields(self, mapping):
        """
        Get the definition of all the current fields we need to calculate the score
        Parameter:
            mapping: Dataframe containing the full mapping of our fields
        Returns a dictionary with:
            key: the custom name of the field as a key
            item: the full definition of the field
        """
        return OrderedDict(
            [
                (
                    row['Current Name'],
                    '{fieldName}={value};'.format(
                        fieldName=row['Current Name'],
                        value=row['Current'].format(fpt=self.periodicity))
                )
                for _, row in mapping.iterrows()
            ]
        )

    def get_change_fields(self, mapping):
        """
        Get the definition of all the current fields we need to calculate the score
        Parameter:
            mapping: Dataframe containing the full mapping of our fields
        Returns a dictionary with:
            key: the custom name of the field as a key
            item: the full definition of the field
        """
        return OrderedDict(
            [
                (
                    row['Change Name'],
                    '{fieldName}={value};'.format(
                        fieldName=row['Change Name'],
                        value=row['Change'].format(
                            fpt=self.periodicity,
                            fpo=self.lookback,
                            lookback=self.lookback,
                            period=self.periodicity if self.periodicity != 'A' else 'Y'
                        ))
                )
                for _, row in mapping.iterrows()
            ]
        )

    def get_scores_def(self, mapping):
        """
        Get the scores definition based on the mapping
        Parameter:
            mapping: Dataframe containing the full mapping of our fields
        Returns a dictionary with:
            key: the custom name of the field as a key
            item: the full definition of the field
        """
        # Get the score names
        scores = mapping['Score'].unique()
        # Build the score definitions
        scores_def = OrderedDict(
            [
                (score,
                 '{score_def}'.format(
                     score_def='+'.join(
                        ['IF({name}*{weight}*{side}>0,1,0)'.format(
                            name=row['Change Name'],
                            weight=row['Weight'],
                            side=row['Side'])
                            for k, row in mapping[mapping['Score'] == score][['Change Name', 'Weight', 'Side']].iterrows()
                        ])))
                for score in scores])
        final_scores = OrderedDict(
            [
                (score, '{score_name}=({score_def})/{weight};'.format(
                    score_name=score,
                    score_def=scores_def[score],
                    weight=mapping[mapping['Score'] == score]['Weight'].sum()
                )) 
                for score in scores
            ]
        )
        return final_scores

    def get_scores_filtered(self, mapping):
        """
        Get the name of the security filtered using matches
        Parameter:
            mapping: Dataframe containing the full mapping of our fields
        Returns a string with the data item
        """
        # Get the score names
        scores = mapping['Score'].unique()
        scores_condition = ' AND '.join(["{}>0".format(score) for score in scores])
        scores_filtered = ['DROPNA(MATCHES({score},{condition}),true) as {score}_filtered'.format(
            score=score,
            condition=scores_condition) for score in scores]
        return """
        DROPNA(MATCHES(#issuer(),{condition}),true).value as #issuer_filtered,
        DROPNA(MATCHES(NAME,{condition}),true) as #name,
        {filtered_scores}""".format(
            condition=scores_condition,
            filtered_scores=','.join(scores_filtered))

    def get_filtered_universe(self):
        """
        Get the base universe based on the spread level and the ticker
        """
        base_univ = "filter(members('{ticker}'{type}), SRCH_ASSET_CLASS=='Corporates')".format(
            ticker=self.ticker,
            type=",type=PORT" if self.ptf_only else ""
        )
        if self.sprd_side != '':
            base_univ = "filter({base_univ},SPREAD(SPREAD_TYPE=G, fill=prev){sprd_side}{sprd_level})".format(
                base_univ=base_univ,
                sprd_side=self.sprd_side,
                sprd_level=self.sprd_level
            )
        return base_univ

    def get_screening_query(self, mapping):
        """
        Get the results of the screening analysis based on:
        -the different user input
        -the different scores
        """
        curr_flds_def = self.get_current_fields(mapping)
        chng_flds_def = self.get_change_fields(mapping)
        score_def = self.get_scores_def(mapping)
        query_def = OrderedDict(chain(curr_flds_def.items(),chng_flds_def.items(),score_def.items()))
        data_item = self.get_scores_filtered(mapping)
        univ = self.get_filtered_universe()

        query = """
        let(
            #issuer=VALUE(ID,issuerof(),mapby=lineage);
            {definition}
            )
        get(
            {data_items}
            )
        for(
            {univ}
            )
        preferences(
            unitscheck=ignore
            )
        """.format(
            definition=''.join([v for _, v in query_def.items()]),
            data_items=data_item,
            univ=univ
        )
        return query

    def get_results_screening(self):
        query = self.get_screening_query(self.config)
        response = self._bq.execute(query)
        return self.combine_dfs(response)

    def get_all_fields(self, query_def):
        """
        Get all the fields for the get query
        """
        return ','.join([k for k, _ in query_def.items()])


    def get_ticker_details(self, ticker):
        """ Retrieve the details of a specific ticker
        Details would be all the current value
        """
        curr_flds_def = self.get_current_fields(self.config)
        chng_flds_def = self.get_change_fields(self.config)
        score_def = self.get_scores_def(self.config)
        query_def = OrderedDict(chain(
            curr_flds_def.items(),
            chng_flds_def.items(),
            score_def.items()))
        get_fields = self.get_all_fields(query_def)
        query = """
        let(
            #issuer=VALUE(ID,issuerof(),mapby=lineage);
            #name=NAME;
            {definition}
            )
        get(
            #name,
            {data_items}
            )
        for(
            ['{univ}']
            )
        preferences(
            unitscheck=ignore
            )
        """.format(
            definition=''.join([v for _, v in query_def.items()]),
            data_items=get_fields,
            univ=ticker
        )
        response = self._bq.execute(query)
        return self.combine_dfs(response)

    def get_ptf_data(self, ptf_id):
        """ Retrieve the portfolio data based on its ID
        """
        univ = self._bq.univ.filter(
            self._bq.univ.members(ptf_id, type='PORT'), self._bq.data.srch_asset_class() == 'Corporates')
        query = bql.Request(univ, {'Name': self._bq.data.name()})
        response = self._bq.execute(query)

        return response.single().df().rename(columns={'ORIG_IDS:0':'Issuer'})

    def run_ptf(self, ptf_id):
        self.data_ptf = self.get_ptf_data(ptf_id)

    def combine_dfs(self, response):
        """    Concatenate in a DataFrame all the response (per column item) from BQL    """
        data = []
        drop_items = ['REVISION_DATE',
                      'AS_OF_DATE',
                      'PERIOD_END_DATE',
                      'CURRENCY',
                      'Partial Errors',
                      'DATE',
                      'ORIG_IDS',
                      'GICS_SECTOR_NAME()',
                      'COUNTRY_FULL_NAME()',
                      'MULTIPLIER',
                      'CPN_TYP']
        for res in response:
            res_df = res.df().drop(drop_items, axis='columns', errors='ignore')
            data.append(res_df)
        return pd.concat(data, axis=1)


    def get_heatmap_query(self, heatmap_toggle):
        """
        Get the query to generate the heatmap of the average of the spread
        """
        base_univ = "members('{ticker}'{type})"
        if heatmap_toggle == 'Financials':
            univ = "filter({}, CLASSIFICATION_NAME('BICS',1)=='Financials')".format(base_univ)
        elif heatmap_toggle == 'Ex-Financials':
            univ = "filter({}, CLASSIFICATION_NAME('BICS',1)!='Financials')".format(base_univ)
        else:
            univ=base_univ
        
        query = """
        let(
            #duration=DURATION(fill=prev);
            #bins=[1,2,3,4,5,6,7,8,9,10,15,20];
            #bin_names=['0-1','1-2','2-3','3-4','4-5','5-6','6-7','7-8','8-9','9-10','10-15','15-20','20+'];
            #duration_buckets=bins(#duration,#bins,#bin_names);
            #avg_spread = AVG(GROUP(SPREAD(SPREAD_TYPE='OAS',fill=prev),[BB_COMPOSITE,#duration_buckets]));
        )
        get(#avg_spread) 
        for(filter({univ}, #duration_buckets!=NA and len(BB_COMPOSITE)>0))
        """.format(
            univ=univ.format(
                ticker=self.ticker,
                type=",type=PORT" if self.ptf_only else "")
        )
        return query

    def get_heatmap_raw_data(self, heatmap_toggle):
        """    Retrieve data model based on the universe and the BQL items    """
        try:
            query = self.get_heatmap_query(heatmap_toggle)
            r = self._bq.execute(query)
            data = self.combine_dfs(r)
        except:
            data = pd.DataFrame()
        return data

    def get_heatmap_formatted_data(self, heatmap_toggle):
        """
        Get the heatmap in a formatted data ready to use
        """
        data = self.get_heatmap_raw_data(heatmap_toggle)
        data.rename(columns={
        'BB_COMPOSITE':'Rating',
        '#DURATION_BUCKETS':'Duration',
        '#avg_spread':'avg(spread)'}, inplace=True)

        # clean the data from NAs for display
        clean_data = data[~data.Rating.isin(['N.A.','NR'])]
        clean_agg_data = clean_data.pivot_table(index='Rating',columns='Duration', values='avg(spread)')
        cols = ['0-1','1-2','2-3','3-4','4-5','5-6','6-7','7-8','8-9','9-10','10-15','15-20','20+']

        # To make sure that all the columns are in the dataframe
        for col in cols:
            if col not in clean_agg_data.columns:
                clean_agg_data[col] = np.nan

        #list of the BBG composite ratings to order the dataframe properly 
        index = ['AAA','AA+','AA','AA-','A+','A','A-','BBB+','BBB','BBB-','BB+','BB','BB-','B+','B','B-','CCC+','CCC','CCC-','CC','C','DDD']

        return clean_agg_data[cols].reindex(index)
    
    def get_heatmap_details(self, rating, duration, heatmap_toggle):
        """
        Get all the securities for the heatmap drilldown
        Parameter:
            rating: Array of ratings
            duration: Array of duration
        """
        base_univ = "members('{ticker}'{type})"
        if heatmap_toggle == 'Financials':
            univ = "filter({}, CLASSIFICATION_NAME('BICS',1)=='Financials')".format(base_univ)
        elif heatmap_toggle == 'Ex-Financials':
            univ = "filter({}, CLASSIFICATION_NAME('BICS',1)!='Financials')".format(base_univ)
        else:
            univ = base_univ

        duration_filter = "['{}']".format("','".join(duration))
        rating_filter = "['{}']".format("','".join(rating))

        curr_flds_def = self.get_current_fields(self.config)
        chng_flds_def = self.get_change_fields(self.config)
        score_def = self.get_scores_def(self.config)
        query_def = OrderedDict(chain(
            curr_flds_def.items(),
            chng_flds_def.items(),
            score_def.items()))
        query = """
        let(
            #issuer=value(NAME, issuerof(),mapby=lineage);
            #duration=DURATION(fill=prev);
            #bins=[1,2,3,4,5,6,7,8,9,10,15,20];
            #bin_names=['0-1','1-2','2-3','3-4','4-5','5-6','6-7','7-8','8-9','9-10','10-15','15-20','20+'];
            #duration_buckets=bins(#duration,#bins,#bin_names);
            {definition}
        )
        get(
            IF(#issuer().value==NA, NAME, #issuer().value) as #issuer_name,
            CPN as #coupon,
            MATURITY as #maturity,
            YIELD(fill=prev) as #ytw,
            SPREAD(SPREAD_TYPE='OAS') as #OAS_spread,
            BB_COMPOSITE as #rating,
            #duration,
            PAYMENT_RANK as #payment_rank,
            #credit_score,
            #valuation_score
        )
        for(
            filter({univ},IN(#duration_buckets,{duration_filter}) AND IN(BB_COMPOSITE,{rating}))
        )
        preferences(
            unitscheck=ignore
        )
        """.format(
            univ=univ.format(
                ticker=self.ticker,
                type=",type=PORT" if self.ptf_only else ""),
            definition=''.join([v for _, v in query_def.items()]),
            duration_filter=duration_filter,
            rating=rating_filter
        )
        response = self._bq.execute(query)
        return self.combine_dfs(response)
