import pandas as pd
import numpy as np
import random

def build_player_profiles(df):
    df = df.copy()

    df['date'] = pd.to_datetime(df['date'])
    df['points'] = pd.to_numeric(df['points'])

    total_days = df['date'].nunique()

    tournament_avg = df[df['points'] > 0].groupby('tournament_type')['points'].mean()

    #Average points, Standard deviation, Attendance rate
    player_avg = df.groupby('player_id')['points'].mean()
    player_std = df.groupby('player_id')['points'].std().fillna(0)
    player_days = df.groupby('player_id')['date'].nunique()

    attendance_alpha = 2
    attendance_beta = 2
    attendance_rate = (player_days + attendance_alpha) / (total_days + attendance_alpha + attendance_beta)

    global_std = df['points'].std()
    if pd.isna(global_std) or global_std == 0:
        global_std = 50
    std_floor = max(global_std * 0.25, 20)
    player_std = player_std.combine(player_avg * 0.15, max).clip(lower=std_floor)

    #low sample penalty
    low_sample_penalty = {}
    for player in player_avg.index:
        games = player_days[player]

        if games >= 5:
            low_sample_penalty[player] = 1
        else:
            low_sample_penalty[player] = games / 5

    #recency attendance momentum
    df_sorted = df.sort_values('date')
    attendance_momentum = {}
    for player, group in df_sorted.groupby('player_id'):
        total_days = df['date'].nunique()
        overall_att = len(group) / total_days
        recent_cutoff = df['date'].max() - pd.Timedelta(days=7)
        recent_games = group[group['date'] >= recent_cutoff]
        possible_recent_days = df[df['date'] >= recent_cutoff]['date'].nunique()

        if possible_recent_days == 0:
            attendance_momentum[player] = 1
            continue
        recent_att = len(recent_games) / possible_recent_days
        if overall_att == 0:
            attendance_momentum[player] = 1
        else:
            attendance_momentum[player] = recent_att / overall_att

    #Average points per tournament type
    player_type_avg = df.groupby(['player_id', 'tournament_type'])['points'].mean()

    player_type_pref = player_type_avg.copy()
    for (player, t_type) in player_type_avg.index:
        global_avg = tournament_avg[t_type]
        player_type_pref[(player, t_type)] = player_type_avg[(player, t_type)] / global_avg

    #bounty metric
    bounty_df = df[df['tournament_type'] == 'bounty']
    bounty_avg = bounty_df.groupby('player_id')['bounties'].mean()
    bounty_counts = bounty_df.groupby('player_id')['bounties'].count()
    global_bounty_avg = bounty_df['bounties'].mean() if len(bounty_df) > 0 else 1
    bounty_skill = {}
    for player in player_avg.index:
        avg = bounty_avg.get(player, global_bounty_avg)
        count = bounty_counts.get(player, 0)
        raw = avg / global_bounty_avg
        shrink = count / (count + 5)
        adjusted = 1 + (raw - 1) * shrink
        adjusted = np.clip(adjusted, 0.7, 1.5)
        bounty_skill[player] = adjusted

    #recency bias metric
    df_sorted = df.sort_values('date')
    recent_form = {}
    recent_dates = sorted(df['date'].unique())[-5:]
    for player in player_avg.index:
        player_games = df_sorted[df_sorted['player_id'] == player]
        recent_games = player_games[player_games['date'].isin(recent_dates)]
        points_list = []
        for d in recent_dates:
            game = recent_games[recent_games['date'] == d]
            if len(game) > 0:
                points_list.append(game['points'].values[0])
            else:
                points_list.append(0)
        recent_avg = np.mean(points_list)
        overall_avg = player_avg[player] if player_avg[player] > 0 else 1
        recent_form[player] = recent_avg / overall_avg

    #experience metric
    max_games = player_days.max()
    experience_weight = (player_days / max_games) ** 0.7

    #clutch metric
    deep_runs = df[df['position'] <= 18]
    player_deep_avg = deep_runs.groupby('player_id')['points'].mean()
    global_deep_avg = deep_runs['points'].mean() if len(deep_runs) > 0 else 1
    clutch_factor = (player_deep_avg / global_deep_avg).fillna(1)

    #field strength metric
    field_strength = {}
    for player, group in df.groupby('player_id'):
        opponents = df[df['date'].isin(group['date'])]
        avg_field = opponents.groupby('player_id')['points'].mean().mean()
        player_avg_points = player_avg[player] if player_avg[player] > 0 else 1
        field_strength[player] = avg_field / player_avg_points

    profiles = {}
    for player in player_avg.index:
        prefs = player_type_pref[player] if player in player_type_pref.index.levels[0] else {}
        prefs_dict = prefs.to_dict() if hasattr(prefs, 'to_dict') else {}

        profiles[player] = {
            'avg_points': float(player_avg[player]),
            'std_points': float(player_std[player]),
            'attendance_rate': float(attendance_rate[player]),
            'tournament_pref': prefs_dict,
            'bounty_skill': float(bounty_skill.get(player, 1)),
            'recent_form': float(recent_form.get(player, 1)),
            'experience': float(experience_weight.get(player, 0.5)),
            'clutch': float(clutch_factor.get(player, 1)),
            'field_strength': float(field_strength.get(player, 1)),
            'attendance_momentum': float(attendance_momentum.get(player, 1)),
            'low_sample': float(low_sample_penalty.get(player, 1))
        }

    return profiles

def build_future_schedule(start_date, end_date):
    WEEKDAY_TO_TYPE = {
        'Wednesday': 'double rating points',
        'Thursday': 'high roller',
        'Friday': 'deep classic',
        'Saturday': 'bounty',
        'Sunday': 'triple shot'
    }

    SPECIAL_BOUNTY_DATES = {}

    dates = pd.date_range(start=start_date, end=end_date)
    schedule = []

    for date in dates:
        date_str = str(date.date())
        day_name = date.day_name()

        if date_str in SPECIAL_BOUNTY_DATES:
            t_type = 'bounty'
        else:
            t_type = WEEKDAY_TO_TYPE.get(day_name)
        if t_type:
            schedule.append({
                'date': date.date(),
                'tournament_type': t_type
            })
    return schedule

def get_current_standings(df):
    latest = df.sort_values('date').groupby('player_id').tail(1)
    latest = latest.sort_values('cumulative_points', ascending=False)
    return {
        row['player_id']: float(row['cumulative_points'])
        for _, row in latest.iterrows()
    }

def simulate_day(standings, profiles, tournament_type, inactive_players=None):
    if inactive_players is None:
        inactive_players = set()
    for player, profile in profiles.items():
        if player in inactive_players:
            continue
        if random.random() > profile['attendance_rate']:
            continue
        mean = profile['avg_points']
        std = profile['std_points']

        if tournament_type in profile['tournament_pref']:
            mean *= profile['tournament_pref'][tournament_type]
        if tournament_type == 'bounty':
            mean *= profile['bounty_skill']
        mean *= (0.7 + 0.3 * profile['recent_form'])
        mean *= (0.6 + 0.4 * profile['experience'])
        mean *= (0.8 + 0.2 * profile['clutch'])
        mean *= (1 / profile['field_strength']) ** 0.2
        mean *= (0.85 + 0.15 * profile['attendance_momentum'])
        mean *= (0.3 + 0.7 * profile['low_sample'])

        points = np.random.normal(mean, std)
        points = max(points, 0)
        standings[player] += points

def simulate_one_run(start_standings, profiles, schedule):
    standings = start_standings.copy()

    cutoff_over_time = []

    for day in schedule:
        simulate_day(standings, profiles, day['tournament_type'])

        ranked = sorted(standings.items(), key=lambda x: x[1], reverse=True)

        cutoff_over_time.append({
            'date': day['date'],
            'cutoff': ranked[18][1]
        })
    return cutoff_over_time

def run_simulations(df, profiles, schedule, n_sim=1000, inactive_players=None):
    start = get_current_standings(df)

    all_cutoffs = []
    all_players = []

    for _ in range(n_sim):
        standings = start.copy()
        cutoff_series = []
        player_series = {}

        for day in schedule:
            simulate_day(standings, profiles, day['tournament_type'], inactive_players=inactive_players)
            ranked = sorted(standings.items(), key=lambda x:x[1], reverse=True)

            cutoff_series.append({
                'date': day['date'],
                'cutoff': ranked[18][1]
            })

            rank_lookup = {p : r for r, (p, _) in enumerate(ranked, 1)}

            for player in standings:
                if player not in player_series:
                    player_series[player] = []
                player_series[player].append({
                    'date': day['date'],
                    'points': standings[player],
                    'rank': rank_lookup[player]
                })
        all_cutoffs.append(cutoff_series)
        all_players.append(player_series)
    return all_cutoffs, all_players

def compute_expected_cutoff(all_cutoffs):
    df = pd.DataFrame([
        {'date': c['date'], 'cutoff': c['cutoff']}
        for sim in all_cutoffs
        for c in sim
    ])

    return df.groupby('date')['cutoff'].mean()

def compute_real_cutoff(df):
    cutoffs = []
    for date in sorted(df['date'].unique()):
        day_df = df[df['date'] <= date]
        latest = day_df.sort_values('date').groupby('player_id').tail(1)
        ranked = latest.sort_values('cumulative_points', ascending=False).reset_index(drop=True)
        cutoff = ranked.iloc[18]['cumulative_points']
        cutoffs.append({
            'date': date,
            'cutoff': cutoff
        })
    return cutoffs

def get_real_player_path(df, player_id):
    df = df.sort_values('date')
    all_dates = sorted(df['date'].unique())

    player_df = df[df['player_id'] == player_id].sort_values('date')
    player_points = []
    last_points = 0

    player_iter = iter(player_df.to_dict('records'))
    current = next(player_iter, None)

    for date in all_dates:
        if current and current['date'] == date:
            last_points = current['cumulative_points']
            current = next(player_iter, None)
        player_points.append({
            'date': date,
            'points': last_points
        })
    return player_points

def compute_expected_player_path(all_player_paths, player_id):
    rows = []
    for sim in all_player_paths:
        player_series = sim[player_id]

        for entry in player_series:
            rows.append({
                'date': entry['date'],
                'points': entry['points']
            })
    df = pd.DataFrame(rows)
    return df.groupby('date')['points'].mean()

def compute_expected_final_ranking(all_players, eval_pool, output_top):
    rank_sum = {}
    count = {}
    for sim in all_players:
        ranked = sorted(
            sim.items(),
            key=lambda x: extract_final_score(x[1]),
            reverse=True
        )[:eval_pool]
        for i, (player, _) in enumerate(ranked):
            rank_sum[player] = rank_sum.get(player, 0) + (i + 1)
            count[player] = count.get(player, 0) + 1
    avg_rank = {
        p: rank_sum[p] / count[p]
        for p in rank_sum
    }

    sorted_players = sorted(avg_rank.items(), key=lambda x: x[1])[:output_top]

    return sorted_players[:output_top]

def compute_expected_player_rank(all_player_paths, player_id):
    rows = []
    for sim in all_player_paths:
        series = sim[player_id]

        for entry in series:
            rows.append({
                'date': entry['date'],
                'rank': entry['rank']
            })
    df = pd.DataFrame(rows)
    return df.groupby('date')['rank'].mean()

def extract_final_score(history):
    if isinstance(history, list) and len(history) > 0:
        last = history[-1]
        if isinstance(last, dict):
            return last.get('points', 0)
    return 0

def get_real_player_rank_path(df, player_id):
    all_dates = sorted(df['date'].unique())

    ranks = []
    last_rank = None

    for date in all_dates:
        day_df = df[df['date'] <= date]
        latest = day_df.sort_values('date').groupby('player_id').tail(1)
        ranked = latest.sort_values('cumulative_points', ascending=False).reset_index(drop=True)
        rank_lookup = {row['player_id']: i+1 for i, row in ranked.iterrows()}
        if player_id in rank_lookup:
            last_rank = rank_lookup[player_id]

        ranks.append({
            'date': date,
            'rank': last_rank
        })
    return ranks

def compute_sample_multiplier(games_played, min_games_for_full=10, min_multiplier=0.22):
    if games_played is None or games_played <= 0:
        return min_multiplier
    if games_played >= min_games_for_full:
        return 1.0
    min_multiplier = max(0.0, min(1.0, min_multiplier))
    span = 1.0 - min_multiplier
    return min_multiplier + (games_played / min_games_for_full) * span


def compute_playoff_odds(all_players, cutoff=18, eval_pool=50, games_played=None, min_games_for_full=10, min_multiplier=0.22):
    first_sim = all_players[0]
    ranked_first = sorted(first_sim.items(), key=lambda x: extract_final_score(x[1]), reverse=True)[:eval_pool]
    players = [p for p, _ in ranked_first]

    rank_counts = {p: [0] * eval_pool for p in players}

    for sim in all_players:
        ranked = sorted(sim.items(), key=lambda x: extract_final_score(x[1]), reverse=True)[:eval_pool]
        for rank, (player, _) in enumerate(ranked):
            if player in rank_counts and rank < eval_pool:
                rank_counts[player][rank] += 1

    df = pd.DataFrame(rank_counts).T
    df.columns = [f'Rank {i+1}' for i in range(eval_pool)]

    df = df / len(all_players)
    df = df.iloc[:, :cutoff]
    df['Top 18 Prob'] = df.sum(axis=1)
    raw_top18_prob = df.sum(axis=1)

    if games_played is not None:
        multipliers = pd.Series({
            player: compute_sample_multiplier(games_played.get(player, 0), min_games_for_full, min_multiplier)
            for player in df.index
        })
    else:
        multipliers = pd.Seroes(1.0, index=df.index)

    df['Top 18 Prob'] = (raw_top18_prob * multipliers).clip(lower=0, upper=1)

    df = df.sort_values(by='Top 18 Prob', ascending=False)
    return df

def is_season_over(today, end_date):
    return pd.to_datetime(today) >= pd.to_datetime(end_date)

def build_final_results(df, player):
    standings = get_current_standings(df)
    ranked = sorted(standings.items(), key=lambda x: x[1], reverse=True)
    real_cutoff = compute_real_cutoff(df)
    real_player = get_real_player_path(df, player)

    final_player_series = {}
    last_date = df['date'].max().date()
    rank_lookup = {p: r for r, (p, _) in enumerate(ranked, 1)}

    for p, pts in standings.items():
        final_player_series[p] = [{
            'date': last_date,
            'points': pts,
            'rank': rank_lookup[p]
        }]
    all_players = [final_player_series]
    return {
        'real_cutoff': real_cutoff,
        'real_player': real_player,
        'sim_cutoff': [],
        'sim_player': [],
        'all_players': all_players
    }