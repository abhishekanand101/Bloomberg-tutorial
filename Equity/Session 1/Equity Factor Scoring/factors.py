# define factors
# Size
def size_mcap(bq):
    field = bq.data.cur_mkt_cap(CURRENCY = 'USD', FILL = 'PREV')/1000000
    return field

# Value
def value_B2M(bq):
    field_01 = 1 / bq.data.px_to_book_ratio(FA_PERIOD_TYPE = 'LTM', FILL = 'PREV')
    field_02 = 1 / bq.data.px_to_book_ratio(FA_PERIOD_TYPE = 'A', FILL = 'PREV')
    field = bq.func.avail(field_01, field_02)
    return field

# momentum
def mom_12M_minus_1M(bq):
    field = bq.data.total_return(CALC_INTERVAL = bq.func.range(START='-12M', END = '-1M'), CURRENCY = 'USD')
    return field

# Volatility factor
def vol_2y_stdev(bq):
    field = bq.data.volatility(CALC_INTERVAL='2Y', CURRENCY = 'USD', PER = 'W')
    return field

# quality
def quality_OP2BE(bq):
    field_01 = (bq.data.is_oper_inc(FA_PERIOD_TYPE = 'LTM', FILL = 'PREV') /
                bq.data.TOT_COMMON_EQY (FA_PERIOD_TYPE = 'LTM', FILL = 'PREV'))
    field_02 = (bq.data.is_oper_inc(FA_PERIOD_TYPE = 'A', FILL = 'PREV') /
                bq.data.TOT_COMMON_EQY (FA_PERIOD_TYPE = 'A', FILL = 'PREV'))
    field = bq.func.avail(field_01, field_02)
    return field