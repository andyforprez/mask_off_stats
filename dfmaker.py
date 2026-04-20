import pandas as pd

def build_cumulative(df):
    df = df.copy()

    df['cumulative_points'] = (
        df.groupby('player_id')['points'].cumsum()
    )
    return df

def expand_player_dates(df):
    all_dates = sorted(df['date'].unique())

    players = df['player_id'].unique()
    full_index = pd.MultiIndex.from_product([players, all_dates], names=['player_id', 'date'])

    df_full = df.set_index(['player_id', 'date']).reindex(full_index).reset_index()

    df_full['cumulative_points'] = df_full.groupby('player_id')['cumulative_points'].ffill()

    df_full['cumulative_points'] = df_full['cumulative_points'].fillna(0)

    return df_full

def add_rankings(df):
    df = df.copy()
    df['rank'] = (
        df.groupby('date')['cumulative_points']
        .rank(method='min', ascending=False)
    )
    return df

def add_daily_gain(df):
    df = df.copy()
    df['daily_gain'] = df.groupby('player_id')['cumulative_points'].diff().fillna(0)
    return df

def make_top100df(df):
    df = df.copy()
    top_100_ids = df.groupby('player_id')['cumulative_points'].max().nlargest(100).index
    return df[df['player_id'].isin(top_100_ids)]