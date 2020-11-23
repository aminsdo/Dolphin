import json
from os import getenv

import requests
from pandas import DataFrame

from algo.asset import Asset
from algo.portfolio import Portfolio
from algo.quote import Quote
from algo.ratio import Ratio

URL = 'https://dolphin.jump-technology.com:8443/api/v1'
# Get credentials
USERNAME = getenv('DOLPHIN_USERNAME', None)
PASSWORD = getenv('DOLPHIN_PASSWORD', None)

START_DATE = '2016-06-01'
END_DATE = '2020-09-30'

AUTH = (USERNAME, PASSWORD)


def get_assets(date: str) -> [Asset]:
    res = requests.get(URL + f'/asset?columns=ASSET_DATABASE_ID&columns=LABEL&columns=LAST_CLOSE_VALUE_IN_CURR&columns=TYPE&date={date}', verify=False, auth=AUTH)
    return [Asset(x, date) for x in res.json()]


def get_quote(start_date: str, end_date: str, asset: Asset) -> [Quote]:
    res = requests.get(URL + f'/asset/{asset.id}/quote?start_date={start_date}&end_date={end_date}', auth=AUTH)
    return [Quote(x) for x in res.json()]


def get_ratios():
    res = requests.get(URL + '/ratio', auth=AUTH)
    return [Ratio(x) for x in res.json()]


def get_sharpe_ratio():
    return get_ratios()[6]


def get_pf_sharpe(asset: Asset):
    rs = get_sharpe_ratio()
    sharpe = calculate_ratio([asset], [rs], START_DATE, END_DATE)
    return sharpe


def get_portfolio(asset: Asset) -> Portfolio:
    res = requests.get(URL + f'/portfolio/{asset.id}/dyn_amount_compo', auth=AUTH)
    return Portfolio(res.json(), asset)


def get_portfolio_quotes(asset: Asset):
    quotes = get_quote(START_DATE, END_DATE, asset)
    l = [x.__dict__ for x in quotes]
    df = DataFrame(l)
    df = df.set_index('date')
    df['return_value'] = df['return']
    return df


def update_portfolio(portfolio: Portfolio) -> bool:
    res = requests.put(URL + f'/portfolio/{portfolio.asset.id}/dyn_amount_compo', auth=AUTH, data=portfolio.json())
    return res.status_code == 200


def calculate_ratio(assets: [Asset], ratios: [Ratio], start_date: str, end_date: str):
    payload = {
        'ratio': [x.id for x in ratios],
        'asset': [x.id for x in assets],
        'bench': None,
        'start_date': start_date,
        'end_date': end_date,
        'frequency': None
    }

    res = requests.post(URL + '/ratio/invoke', data=json.dumps(payload), auth=AUTH)
    ratio_res = {}
    for asset_id, ratios in res.json().items():
        if asset_id not in ratios:
            ratio_res[asset_id] = {}
        for ratio_id, value in ratios.items():
            ratio_res[asset_id][ratio_id] = float(value['value'].replace(',', '.'))

    return ratio_res


def get_currency_rate(src: str, dst: str, date: str):
    payload = {'fullResponse': True, 'date': date}
    res = requests.get(URL + f'/currency/rate/{src}/to/{dst}', auth=AUTH, params=payload)
    return float(res.json()['rate']['value'].replace(',', '.'))

