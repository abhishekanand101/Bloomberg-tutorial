def get_fields(bq):
    return {
        'Market cap limit (in mln USD)' : bq.data.market_cap(currency='USD') / 1000000,
        'Daily liquidity (in mln)' : bq.data.turnover(start='-30d',currency='USD').avg() / 1000000,
        'ROE limit (%)' : bq.data.return_com_eqy(),
        'EBITDA CAGR 5y limit (%)' : bq.data.ebitda(fpo=bq.func.range('-5','0')).compoundgrowthrate() * 100
    }

def get_grouping_fields(bq):
    return {
        'GICS Sector': bq.data.classification_name('GICS', '1'),
        'BICS Sector': bq.data.BICS_LEVEL_1_SECTOR_NAME(),
        'BICS Industry': bq.data.BICS_LEVEL_3_INDUSTRY_NAME(),
    }

def get_additional_fields(bq):
    return {
        'Name': bq.data.name(),
        'Country': bq.data.country_full_name(),
        'Price (USD)': bq.data.px_last(currency='USD', fill='prev'),
        'EPS FY0': bq.data.is_eps(fpt='A'),
        'EPS FY1': bq.data.is_eps(fpt='A', fpo='1'),
        'EPS FY2': bq.data.is_eps(fpt='A', fpo='2'),
        'Revenue FY0 (in mln USD)': bq.data.sales_rev_turn(fpt='A', currency='USD')/1000000,
        'Revenue Growth FY-1/FY0': bq.data.sales_rev_turn(fpt='A', fpo=bq.func.range('-1','0')).pct_chg()/100,
        'Revenue Est Growth FY0/FY1': bq.data.sales_rev_turn(fpt='A', fpo=bq.func.range('0','1')).pct_chg()/100,
        'Dividend Per Sh': bq.data.is_div_per_shr(fpt='A'),
        'Upside (Consensus)': bq.data.best_target_price(fill='prev')/bq.data.px_last(fill='prev')-1,
        'Total Rec': bq.data.tot_analyst_rec(),
        'Buy Rec': bq.data.tot_buy_rec()/bq.data.tot_analyst_rec(),
        'Hold Rec': bq.data.tot_hold_rec()/bq.data.tot_analyst_rec(),
        'Sell Rec': bq.data.tot_sell_rec()/bq.data.tot_analyst_rec(),
        'Consensus Rating':  bq.data.best_analyst_rating(),
        'ESG MSCI Rating': bq.data.esg_rating(rating_source='MSCI')
    }
