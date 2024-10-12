import bql 

class DataModel(object):
    '''
    DataModel class for retrieval of bql fields used by app
    '''
        
    def __init__(self):
        self._bq = bql.Service() 
    
    def initialise_model(self, dict_univ, start_date, end_date):
        '''
        Function to initialise a DataModel object 
        
        Parameters:
        -----------
        dict_univ: dictionary of the screening universe 
        start_date: start date for data retrieval 
        end_date: end date for data retrieval 
        '''
        
        value = list(filter(None,dict_univ['value']))
        if dict_univ['type'] == 'Index':
            self.univ = self._bq.univ.members(value)
        else:
            self.univ = self._bq.univ.list(value)
        # self.univ = self._bq.univ.members(univ) if type(univ) == str else univ 
        self.start_date = start_date
        self.end_date = end_date
    
    def run(self):
        '''
        Function to retrieve bql fields used by app
        
        Returns
        -------
        dictionary of bql fields 
        '''
        
        fields = {
            'price': self._bq.data.px_last(ca_adj='full',dates=self._bq.func.range(start = self.start_date, end = self.end_date, frq='D'), fill='PREV', currency='USD' ), 
            'first_diff': self._bq.data.px_last(ca_adj='full',dates=self._bq.func.range(start = self.start_date,  end = self.end_date, frq='D'), fill='PREV',currency='USD').diff(),
            'log_price': self._bq.data.px_last(ca_adj='full',dates=self._bq.func.range(start = self.start_date, end = self.end_date, frq='D'),fill='PREV',currency='USD').ln()
        }
        
        res = self._bq.execute(bql.Request(self.univ, fields))
        self.price = res.get('price').df().reset_index().pivot_table(values='price', index='DATE', columns='ID')
        self.first_diff = res.get('first_diff').df().reset_index().pivot_table(values='first_diff', index='DATE', columns='ID')
        self.log_price = res.get('log_price').df().reset_index().pivot_table(values='log_price', index='DATE', columns='ID')
        self.univ_tickers = list(self.price.columns.values)
        self.dates = list(self.price.index)
        
        return {
            'price': self.price,
            'first_diff': self.first_diff,
            'log_price': self.log_price,
            'univ_tickers': self.univ_tickers,
            'dates': self.dates
        } 
