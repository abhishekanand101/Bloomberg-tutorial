def get_operator_functions(bq):
    '''
    Returns a dictionary with sign as key and bql function as value
    '''
    return {
        '>': bq.func.greater,
        '<': bq.func.less,
        '=': bq.func.equals
    }

def apply_scoring_function(bq, field, function_name, grouping=[]):
    '''
    Returns a bql item 
    '''
    if function_name=='Percentile':
        score = bq.func.group(field,grouping).cut(100).ungroup()
    else:
        # by default do Zscore
        score = bq.func.groupzscore(field,grouping) 
    return score
    
    