from collections import OrderedDict


PERIODICITY = ['Annual', 'Semi-Annual', 'Quarterly']

# UNIVERSE = "filter({universe}, srch_asset_class=='Corporates')"

# BARCLAYS_INDEX = OrderedDict([
#     ('Global Aggregate Credit','LGDRTRUU Index'),
#     ('US Universal','LC07TRUU Index'),
#     ('US Aggregate','LBUSTRUU Index'),
#     ('US Government/Credit','LUGCTRUU Index'),
#     ('US Government-Related','LD08TRUU Index'),
#     ('Corporate','LUACTRUU Index'),
#     ('Pan-Euro Aggregate','LP06TREU Index'),
#     ('Euro Aggregate','LBEATREU Index'),
#     ('Asian Pacific Aggregate','LAPCTRJU Index'),
#     ('Global High Yield','LG30TRUU Index'),
#     ('US High Yield','LF98TRUU Index'),
#     ('Global Aggregate','LEGATRUU Index'),
#     ('Pan-European High Yield','LP01TREU Index'),
#     ('EM USD Aggregate','EMUSTRUU Index'),
#     ('China Aggregate','LACHTRUU Index'),
#     ('Canada Aggregate','I05486CA Index')    
# ])

SIDE_OPTIONS = [
    ('Higher the better', 1),
    ('Lower the better', -1)
]

TEMPLATE_DETAILS = """
<table border='1'>
<thead>
<tr>
<th style='text-align:center;' colspan='3'>
{name}
</th>
</tr>
<tr>
<th>{score_name} Component</th>
<th>Current Value</th>
<th>Change</th>
<tr>
</thead>
<tbody>
{body}
</tbody>
<tfooter>
<tr>
<td><span style='font-weight:bold;'>{score_name}</span></td>
<td><span style='font-weight:bold;'>{score_value: .3f}</span></td>
</tr>
</tfooter>
"""

TEMPLATE_DETAILS_LINE = """
<tr>
<td>{field}</td>
<td>{current:.2f}</td>
<td>{change}</td>
</tr>
"""

SUMMARY_SCREEN = """
<table border='1'>
<thead>
<tr>
<th style='text-align:center;' colspan='2'>
Screening Summary
</th>
</tr>
</thead>
<tbody>
<tr>
<td>Average Credit Score</th>
<td>{avg_credit_score: .3f}</th>
</tr>
<tr>
<td>Average Valuation & Metrics</th>
<td>{avg_valuation_score: .3f}</th>
</tr>
<tr>
<td>Total Number of Bonds</th>
<td>{nb_bonds}</th>
</tr>
<tr>
<td>Total Number of Issuers</th>
<td>{nb_issuer}</th>
</tr>
</tbody>
"""
