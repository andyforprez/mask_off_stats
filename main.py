from analysis import *
from dfmaker import *
from simulations.pipeline import *
import pandas as pd

df = pd.read_csv('data/raw_data.csv')
df['date'] = pd.to_datetime(df['date'])

df = build_cumulative(df)
full_df = expand_player_dates(df)
top100_df = make_top100df(df)
rank_df = add_rankings(full_df)
gain_df = add_daily_gain(df)

today = df['date'].max()
player = 'Антуан Гризманн'
inactive_players = {
    'Дядя Витя',
    'Кесадилия',
    'Комарик'
}

def graphs():
    player_ranking_over_time(full_df, 'Антуан Гризманн')
    top_players_points_comparison(full_df, 18)
    top_players_rankings_comparison(rank_df, 18)
    type_averages(df)
    points_distribution(df, 18, 50)
    volatility_std(df, 18, 5)
    plot_cutoff(full_df, 'Антуан Гризманн')
    best_days(df, 18)
    attendance(df, 18)
    consistency_vs_attendance(df, 18, 5)
save_ranking_by_date(df, today)
save_averages(df)

result = run_full_simulation(df, player, n_sim=1000, inactive_players=inactive_players)

plot_cutoff_projection(result['real_cutoff'], result['sim_cutoff'], today, player, result['real_player'], result['sim_player'])
run_rank_projection_pipeline(df, result['all_players'], today, 50, True, 100)
run_playoff_odds_pipeline(result['all_players'], 19, 30, True, True)