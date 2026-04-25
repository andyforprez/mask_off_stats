import matplotlib.pyplot as plt
from collections import defaultdict
import pandas as pd


def save_ranking_by_date(df, target_date, path='data/rankings.txt'):
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    target_date = pd.to_datetime(target_date)

    last_points = {}
    games_count = defaultdict(int)

    df_filtered = df[df['date'] <= target_date]
    for _, row in df_filtered.iterrows():
        player = row['player_id']
        last_points[player] = int(row['cumulative_points'])
        games_count[player] += 1

    sorted_players = sorted(last_points.items(), key=lambda x: x[1], reverse=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f'RANKING AS OF {target_date.date()}\n')
        f.write('=' * 50 + '\n\n')
        for rank, (player, points) in enumerate(sorted_players, 1):
            f.write(
                f'{rank}. {player} - {points} points ({games_count[player]} games)\n'
            )
    print(f'Rankings saved to {path}')
    return sorted_players

def save_averages(df, min_games=5, path='data/averages.txt'):
    stats = df.groupby('player_id').agg(
        total_points=('points', 'sum'),
        games_played=('points', 'count')
    )
    stats['avg_points'] = stats['total_points'] / stats['games_played']
    stats = stats[stats['games_played'] > min_games]
    stats = stats.sort_values(by='avg_points', ascending=False)
    with open(path, 'w', encoding='utf-8') as f:
        f.write('AVERAGE POINTS PER GAME\n')
        f.write('=' * 50 + '\n\n')
        for i, (player, row) in enumerate(stats.iterrows(), 1):
            avg = row[('avg_points')]
            games = int(row['games_played'])
            total = int(row['total_points'])
            f.write(f'{i}. {player} - {avg:.2f} avg\n')
    print(f'Averages saved to {path}')

def player_ranking_over_time(df, player_name):
    player_df = df[df['player_id'] == player_name]

    plt.figure()
    plt.plot(player_df['date'], player_df['cumulative_points'])
    plt.title('My Points Over Time')
    plt.xlabel('Date')
    plt.ylabel('Points')
    plt.grid(axis='y')
    plt.show()

def top_players_points_comparison(df, top_n):
    top_players = (
        df.groupby('player_id')['cumulative_points'].max().nlargest(top_n).index
    )
    plt.figure()
    for player in top_players:
        temp = df[df['player_id'] == player]
        plt.plot(temp['date'], temp['cumulative_points'], alpha=0.6, label=player)
        last_row = temp.iloc[-1]
        plt.text(
            last_row['date'],
            last_row['cumulative_points'],
            f'{player} ({int(last_row['cumulative_points'])})',
            fontsize=5
        )

    plt.title(f'Top {top_n} Players Over Time')
    plt.xlabel('Date')
    plt.ylabel('Points')
    plt.legend(fontsize=6, ncol=2)
    plt.grid(axis='y')
    plt.show()

def top_players_rankings_comparison(df, top_n):
    top_players = (
        df.groupby('player_id')['cumulative_points'].max().nlargest(top_n).index
    )

    plt.figure()
    for player in top_players:
        temp = df[df['player_id'] == player]
        plt.plot(temp['date'], temp['rank'], alpha=0.6, label=player)
        last_row = temp.iloc[-1]
        plt.text(
            last_row['date'],
            last_row['rank'],
            f'{player} ({int(last_row['rank'])})',
            fontsize=5
        )

    plt.gca().invert_yaxis()
    plt.title(f'Top {top_n} Player Rankings Over Time')
    plt.xlabel('Date')
    plt.ylabel('Rank')
    plt.grid(axis='y')
    plt.ylim(25, 0)
    plt.legend(fontsize=6, ncol=3)
    plt.show()

def type_averages(df, top_n=None, min_points=None):
    df_filtered = df.copy()
    if top_n is not None:
        top_players = df.groupby('player_id')['cumulative_points'].max().nlargest(top_n).index
        df_filtered = df[df['player_id'].isin(top_players)]

    if min_points is not None:
        df_filtered = df_filtered[df_filtered['points'] > min_points]

    avg_by_type = df_filtered.groupby('tournament_type')['points'].mean()
    plt.figure()
    avg_by_type.plot(kind='bar')
    title = 'Average Points by Tournament Type'
    if top_n:
        title += f' (Top {top_n} Players)'
    if min_points:
        title += f' | Over {min_points} Points'
    plt.title(title)
    plt.xlabel('Tournament Type')
    plt.ylabel('Average Points')
    plt.xticks(fontsize=6)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()

def points_distribution(df, top_n=None, min_points=None):
    df_filtered = df.copy()
    if top_n is not None:
        top_players = df.groupby('player_id')['cumulative_points'].max().nlargest(top_n).index
        df_filtered = df[df['player_id'].isin(top_players)]

    if min_points is not None:
        df_filtered = df_filtered[df_filtered['points'] >= min_points]

    plt.figure()
    df_filtered['points'].hist(bins=50)
    title = 'Points Distribution'
    if top_n:
        title += f' (Top {top_n} Players)'
    if min_points:
        title += f' | Over {min_points} Points'
    plt.title(title)
    plt.xlabel('Points per Game')
    plt.ylabel('Frequency')
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()

def volatility_std(df, top_n, min_games):
    valid_players = df.groupby('player_id')['date'].count()
    valid_players = valid_players[valid_players >= min_games].index

    df_filtered = df[df['player_id'].isin(valid_players)]

    top_players = df_filtered.groupby('player_id')['cumulative_points'].max().nlargest(top_n).index

    volatility = (
        df_filtered[df_filtered['player_id'].isin(top_players)]
        .groupby('player_id')['points']
        .std()
        .sort_values(ascending=False)
    )

    plt.figure()
    volatility.plot(kind='bar')

    plt.title(f'Top {top_n} Least Volatile Players')
    plt.xlabel('Player')
    plt.ylabel('Std Dev of Daily Gain')
    plt.xticks(rotation=90)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()

def mean_points(df, top_n, min_games):
    valid_players = df.groupby('player_id')['date'].count()
    valid_players = valid_players[valid_players >= min_games].index

    df_filtered = df[df['player_id'].isin(valid_players)]

    top_players = df_filtered.groupby('player_id')['cumulative_points'].max().nlargest(top_n).index

    avg = (
        df_filtered[df_filtered['player_id'].isin(top_players)]
        .groupby('player_id')['points']
        .mean()
        .sort_values(ascending=False)
    )

    plt.figure()
    avg.plot(kind='bar')

    plt.title(f'Top {top_n} Most Consistent Players')
    plt.xlabel('Player')
    plt.ylabel('Average Points')
    plt.xticks(rotation=90)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()

def plot_cutoff(df, player_name=None):
    df = df.copy()
    if 'date' not in df.columns:
        df = df.reset_index()

    df = df.sort_values(['date', 'cumulative_points'], ascending=[True, False])
    cutoff = df.groupby('date', as_index=False).nth(18)
    cutoff = cutoff.reset_index(drop=True)

    plt.figure()
    plt.plot(cutoff['date'], cutoff['cumulative_points'], label='Top 18 Cutoff')

    if player_name is not None:
        player_df = df[df['player_id'] == player_name]
        plt.plot(
            player_df['date'],
            player_df['cumulative_points'],
            label=player_name
        )
        plt.legend()
    title = "Cutoff"
    if player_name:
        title += f' vs {player_name} Points'
    plt.title(title)
    plt.xlabel('Date')
    plt.ylabel('Points')
    plt.xticks(rotation=90)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()

def best_days(df, top_n):
    best = df.sort_values('points', ascending=False).head(top_n)
    labels = best['player_id'] + ' (' + best['date'].astype(str) + ')'

    plt.figure()
    plt.bar(labels, best['points'])

    plt.title(f'Top {top_n} Best Single-Day Performances')
    plt.xlabel('Player (Date)')
    plt.ylabel('Points')
    plt.xticks(rotation=90, fontsize=8)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()

def attendance(df, top_n):
    attendance = df.groupby('player_id')['date'].nunique().sort_values(ascending=False).head(top_n)
    plt.figure()
    attendance.plot(kind='bar')

    plt.title(f'Top {top_n} Most Active Players')
    plt.xlabel('Player')
    plt.ylabel('Rate Played')
    plt.xticks(rotation=90, fontsize=8)
    plt.grid(axis='y')
    plt.tight_layout()
    plt.show()

def consistency_vs_attendance(df, top_n, min_games):
    valid_players = df.groupby('player_id')['date'].count()
    valid_players = valid_players[valid_players >= min_games].index

    df_filtered = df[df['player_id'].isin(valid_players)]

    top_players = df_filtered.groupby('player_id')['cumulative_points'].max().nlargest(top_n).index

    consistency = df_filtered.groupby('player_id')['points'].std()
    attendance = df_filtered.groupby('player_id')['date'].nunique()

    merged = consistency.to_frame('consistency').join(attendance.to_frame('attendance'))
    merged = merged.loc[top_players]

    plt.figure()
    plt.scatter(merged['attendance'], merged['consistency'])

    for player in merged.index:
        plt.text(
            merged.loc[player, 'attendance'] + 0.1,
            merged.loc[player, 'consistency'],
            player,
            fontsize=6
        )

    plt.xlabel('Days Played')
    plt.ylabel('Volatility')
    plt.title(f'Top {top_n} Players: Consistency vs Attendance')
    plt.tight_layout()
    plt.show()