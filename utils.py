import pandas as pd

MICROSECONDS_MULTIPLIER = 1_000_000

BASE_CPP_ORDER_BOOK_VARIABLES = [
    'timestampOfReceive',
    'market',
    'symbol',
    'streamType',
    'bestAskPrice',
    'bestBidPrice',
    'midPrice'
]

def calculate_mid_price_diff(df: pd.DataFrame, mid_price_diff_seconds: int) -> pd.Series:
    shifted = df[['timestampOfReceive', 'midPrice']].copy()
    shifted['timestampOfReceive'] -= mid_price_diff_seconds * 1_000_000

    merged = pd.merge_asof(
        df[['timestampOfReceive', 'midPrice']],
        shifted,
        on='timestampOfReceive',
        suffixes=('', '_shifted'),
        direction='backward'
    )

    return (merged['midPrice_shifted'] - merged['midPrice']).round(8)

def calculate_highest_and_lowest_mid_price_diff(df: pd.DataFrame, mid_price_diff_seconds: int) -> (pd.Series, pd.Series):
    real_diff = mid_price_diff_seconds * MICROSECONDS_MULTIPLIER + 1
    temp = df.iloc[::-1].copy().reset_index(drop=True)

    temp['timestampOfReceive_dt'] = pd.to_datetime(temp['timestampOfReceive'], unit='us')

    temp[f'h'] = temp.rolling(f'{real_diff}us', on='timestampOfReceive_dt', min_periods=1)['midPrice'].max()
    temp[f'l'] = temp.rolling(f'{real_diff}us', on='timestampOfReceive_dt', min_periods=1)['midPrice'].min()

    temp['h_diff'] = (temp['h'] - temp['midPrice']).round(2)
    temp['l_diff'] = (temp['l'] - temp['midPrice']).round(2)

    temp.drop(['h', 'l'], axis=1, inplace=True)

    temp = temp[::-1].reset_index(drop=True)

    return temp['h_diff'].rename(None), temp['l_diff'].rename(None)

def calculate_highest_mid_price_diff(df: pd.DataFrame, mid_price_diff_seconds: int) -> pd.Series:
    h, _ = calculate_highest_and_lowest_mid_price_diff(df, mid_price_diff_seconds)
    return h

def calculate_lowest_mid_price_diff(df: pd.DataFrame, mid_price_diff_seconds: int) -> pd.Series:
    _, l = calculate_highest_and_lowest_mid_price_diff(df, mid_price_diff_seconds)
    return l

def calculate_h_minus_l_prediction(df: pd.DataFrame, mid_price_diff_seconds: int) -> pd.Series:
    h, l = calculate_highest_and_lowest_mid_price_diff(df, mid_price_diff_seconds)
    hl_diff = (h - l).round(2)
    return hl_diff
