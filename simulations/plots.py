import matplotlib.pyplot as plt
import pandas as pd

def plot_cutoff_projection(real, sim, today, player_id=None, real_player=None, sim_player=None):
    real_dates = [x['date'] for x in real]
    real_cutoffs = [x['cutoff'] for x in real]
    sim_dates = [x['date'] for x in sim]
    sim_cutoffs = [x['cutoff'] for x in sim]

    last_real_date = real_dates[-1]
    last_real_cutoff = real_cutoffs[-1]
    sim_dates.insert(0, last_real_date)
    sim_cutoffs.insert(0, last_real_cutoff)

    plt.figure(figsize=(10, 5))
    plt.plot(real_dates, real_cutoffs, color='blue', label='Actual Cutoffs')
    plt.plot(sim_dates, sim_cutoffs, color='blue', label='Projected Cutoffs')

    if player_id and real_player and sim_player:
        rp_dates = [x['date'] for x in real_player]
        rp_points = [x['points'] for x in real_player]
        sp_dates = [x['date'] for x in sim_player]
        sp_points = [x['points'] for x in sim_player]

        sp_dates.insert(0, rp_dates[-1])
        sp_points.insert(0, rp_points[-1])

        plt.plot(rp_dates, rp_points, color='red', linestyle='--', label=f'{player_id} (Actual)')
        plt.plot(sp_dates, sp_points, color='red', linestyle='--', label=f'{player_id} (Projected)')

    plt.xlabel('Date')
    plt.ylabel('Points')
    plt.axvline(pd.to_datetime(today), color='green', linestyle='--')
    title = 'Expected Cutoff Projection'
    if player_id and real_player and sim_player:
        title += f' vs {player_id}'
    plt.title(title)
    plt.legend()
    plt.xticks(rotation=45)
    plt.grid(axis='y')
    plt.show()

def plot_player_rank_over_time(expected_rank, real_rank, player_id):
    exp_dates = list(expected_rank.index)
    exp_ranks = list(expected_rank.values)

    real_dates = [x['date'] for x in real_rank]
    real_ranks = [x['rank'] for x in real_rank]

    plt.figure(figsize=(10, 5))
    plt.plot(real_dates, real_ranks, linestyle='--', label='Actual Rank')
    plt.plot(exp_dates, exp_ranks, linestyle='--', label='Projected Rank')
    plt.gca().invert_yaxis()
    plt.title(f'Rank Progression: {player_id}')
    plt.xlabel('Date')
    plt.ylabel('Rank')
    plt.legend()
    plt.xticks(rotation=90)
    plt.grid(axis='y')
    plt.show()

def plot_rank_projections(real_rank, sim_rank, today, player_id):
    real_dates = [x['date'] for x in real_rank]
    real_ranks = [x['rank'] for x in real_rank]

    sim_dates = list(sim_rank.index)
    sim_ranks = list(sim_rank.values)

    sim_dates.insert(0, real_dates[-1])
    sim_ranks.insert(0, real_ranks[-1])

    plt.figure(figsize=(10, 5))
    plt.plot(real_dates, real_ranks, label='Actual Rank')
    plt.plot(sim_dates, sim_ranks, label='Projected Rank')
    plt.axvline(pd.to_datetime(today), linestyle='--')
    plt.gca().invert_yaxis()
    plt.xlabel('Date')
    plt.ylabel('Rank')
    plt.title(f'Projected Rank Progression: {player_id}')
    plt.legend()
    plt.xticks(rotation=90)
    plt.grid(axis='y')
    plt.show()

def plot_rank_projections_multi(real_ranks_dict, sim_ranks_dict, today, top_n=None):
    plt.figure(figsize=(12, 6))

    players = list(sim_ranks_dict.keys())
    if top_n:
        players = players[:top_n]

    cmap = plt.get_cmap('tab20')
    colors = {player: cmap(i % 20) for i, player in enumerate(players)}

    for player in players:
        sim_rank = sim_ranks_dict[player]
        real_rank = real_ranks_dict[player]

        sim_dates = list(sim_rank.index)
        sim_values = list(sim_rank.values)

        real_dates = [x['date'] for x in real_rank]
        real_values = [x['rank'] for x in real_rank]

        sim_dates.insert(0, real_dates[-1])
        sim_values.insert(0, real_values[-1])

        color = colors[player]

        plt.plot(sim_dates, sim_values, color=color, linestyle='--', label=player)
        plt.plot(real_dates, real_values, color=color)
    plt.axvline(today, color='black', linestyle='--')
    plt.gca().invert_yaxis()
    plt.ylim(40, 0)
    plt.xlabel('Date')
    plt.ylabel('Rank')
    plt.title('Projected Rank Progression')

    plt.legend(fontsize=4)
    plt.xticks(rotation=90)
    plt.grid(axis='y')
    plt.show()







