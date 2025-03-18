import pandas as pd
import os, sys, re
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify 
from loguru import logger
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from waitress import serve

script_dir = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(script_dir, '..')))

from sql_utils.sql_transfers import *

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key_for_testing')

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per minute"]
)

def get_version():
    try:
        with open('version.txt', 'r') as f:
            version = f.read().strip()
        return version
    except Exception as e:
        print(f"Error reading version file: {e}")
        return "v?.?.?"
    
version = get_version()

# utils functions

def replace_team_for_traded_players(df):
    if df.empty or 'team' not in df.columns or len(df) < 2:
        return df  # return as is if empty or has less than 2 rows

    top_team = df.iloc[0]['team']
    latest_team = df.iloc[-1]['team']

    # check if top_team follows the 'NTM' pattern
    if re.match(r'^\dTM$', str(top_team)):
        df.at[df.index[0], 'team'] = latest_team  # replace with second team's value

    df = df.head(1)

    return df

def season_to_year(season: str) -> int:
    start_year, end_year_suffix = season.split('-')
    start_year = int(start_year)
    if end_year_suffix == "00":
        end_year = start_year + 1
    else:
        if int(end_year_suffix) < int(str(start_year)[-2:]):
            end_year = int(str(start_year)[:2] + end_year_suffix)
        else:
            end_year = start_year + 1
    return end_year

def calc_nba_payroll(total_teams: int, salary_cap: float) -> float:
    """Calculates the total NBA payroll."""
    return float(total_teams) * float(salary_cap)

def calc_value_of_win_share(nba_payroll: float, total_wins: int) -> float:
    """Calculates the monetary value of one win share."""
    return nba_payroll / float(total_wins)

def calc_salary_per_win_share(salary: float, win_shares: float) -> float:
    """Calculates how much a player earns per win share."""
    if win_shares != 0.0 and win_shares > 0.0:
        return float(salary) / float(win_shares)
    elif win_shares < 0.0:
        return 0.0
    else:
        return 0.0

def calc_overpay_index(salary_per_ws: float, value_of_ws: float) -> float:
    """Calculates the overpay index based on salary per WS vs league average."""
    return round((salary_per_ws / value_of_ws), 2)

def calc_adjusted_salary(salary: float, overpay_index: float) -> float:
    """Calculates the adjusted salary based on value per WS."""
    if overpay_index != 0:
        return (1 / overpay_index) * salary
    else:
        return 0.0

def calc_contract_value_rating(overpay_index, max_overpay_index=10.0):

    if overpay_index != 0:

        max_overpay_index = max(max_overpay_index, 1.1)

        # normalize overpay index to 0.0 - 5.0 scale
        if overpay_index <= 1.0:
            contract_value_rating = 5.0  # "perfect" contract
        else:
            contract_value_rating = max(0.0, 5.0 * (1 - ((overpay_index - 1) / (max_overpay_index - 1))))

        return round(contract_value_rating, 2)
    
    else:
        return 0.0

def format_to_dollars(amount: float) -> str:
    return f"${amount:,.2f}"

def format_to_short_dollar(amount: float) -> str:
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.2f}B"
    elif amount >= 1_000_000:
        return f"${amount / 1_000_000:.2f}M"
    elif amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    else:
        return f"${amount:.2f}"

def pct_diff(old: float, new: float) -> str:
    """Calculates the percentage difference between two values."""
    if old == 0:
        return "0"  # return 0 if the old value is 0 to avoid division by zero
    try:
        diff: float = ((new - old) / abs(old)) * 100
        sign: str = "+" if diff >= 0 else "-"
        return f"{sign}{abs(diff):.2f}"
    except Exception as e:
        logger.error(f"Error calculating percentage difference: {e}")
        return "0"
    
def money_to_float(s):
    """Convert string with $ and commas to a float variable."""
    try:
        return float(s.replace("$", "").replace(",", ""))
    except Exception as e:
        logger.error(f"Error converting money string to float: {e}")
        return 0.0

def analyze_player(season, player_id):
    """Main function to analyze player contract value"""
    if not season or not player_id:
        raise ValueError("Season and player ID are required")
        
    logger.info(f"Analyzing player {player_id} for season {season}")
    
    try:
        year = season_to_year(season)
        if year is None:
            raise ValueError(f"Invalid season format: {season}")
        
        # extract data from database
        logger.info(f"Extracting data for {player_id} in season {season} (year {year})")
        year = season_to_year(season)

        salary_data_df = extract_table_to_df(f'{year}_player_salaries', 'salary')
        pergame_stats_df = extract_table_to_df(f'{year}_reg_season_stats', 'per_game_stats')
        adv_stats_df = extract_table_to_df(f'{year}_reg_season_stats', 'advanced_stats')

        salary_caps_df = extract_table_to_df('salary_caps', 'salary')
        league_team_wins_df = extract_table_to_df('league_wins_teams', 'salary')

        player_salary_df = salary_data_df[salary_data_df['player_id'] == player_id]
        pergame_stats_df = pergame_stats_df[pergame_stats_df['player_id'] == player_id]
        adv_stats_df = adv_stats_df[adv_stats_df['player_id'] == player_id]

        player_salary_df = player_salary_df.head(1)
        pergame_stats_df = replace_team_for_traded_players(pergame_stats_df)
        adv_stats_df = replace_team_for_traded_players(adv_stats_df)

        player_name = pergame_stats_df['player_name'].iloc[0]
        logger.debug(f"player_name = {player_name}, type = {type(player_name)}")

        age = pergame_stats_df['age'].iloc[0]
        logger.debug(f"age = {age}, type = {type(age)}")

        team = pergame_stats_df['team'].iloc[0]
        logger.debug(f"team = {team}, type = {type(team)}")

        salary = player_salary_df['salary'].iloc[0]
        logger.debug(f"salary = {salary}, type = {type(salary)}")

        salary_short = format_to_short_dollar(money_to_float(salary))
        logger.debug(f"salary_short = {salary_short}, type = {type(salary_short)}")

        win_shares = adv_stats_df['win_shares'].iloc[0]
        logger.debug(f"win_shares = {win_shares}, type = {type(win_shares)}")

        salary_cap_row = salary_caps_df[salary_caps_df['season'] == season]
        logger.debug(f"salary_cap_row.shape = {salary_cap_row.shape}")

        salary_cap = salary_cap_row['salary_cap'].iloc[0]
        logger.debug(f"salary_cap = {salary_cap}, type = {type(salary_cap)}")

        salary_cap_short = format_to_short_dollar(money_to_float(salary_cap))
        logger.debug(f"salary_cap_short = {salary_cap_short}, type = {type(salary_cap_short)}")

        league_team_wins_row = league_team_wins_df[league_team_wins_df['year'] == year]
        logger.debug(f"league_team_wins_row.shape = {league_team_wins_row.shape}")

        total_teams = league_team_wins_row['total_teams'].iloc[0]
        logger.debug(f"total_teams = {total_teams}, type = {type(total_teams)}")

        total_wins = league_team_wins_row['total_wins'].iloc[0]
        logger.debug(f"total_wins = {total_wins}, type = {type(total_wins)}")

        logger.debug(f"Before nba_payroll calculation - total_teams = {total_teams}, salary_cap = {salary_cap}")
        logger.debug(f"money_to_float(salary_cap) = {money_to_float(salary_cap)}")
        raw_nba_payroll = calc_nba_payroll(total_teams, money_to_float(salary_cap))
        logger.debug(f"raw_nba_payroll = {raw_nba_payroll}, type = {type(raw_nba_payroll)}")

        nba_payroll = format_to_dollars(raw_nba_payroll)
        logger.debug(f"nba_payroll = {nba_payroll}, type = {type(nba_payroll)}")

        logger.debug(f"Before nba_payroll_short calculation - nba_payroll = {nba_payroll}")
        logger.debug(f"money_to_float result of nba_payroll = {money_to_float(nba_payroll)}")
        nba_payroll_short = format_to_short_dollar(money_to_float(nba_payroll))
        logger.debug(f"nba_payroll_short = {nba_payroll_short}, type = {type(nba_payroll_short)}")

        # keep raw values for calculations
        raw_nba_avg_salary_per_ws = calc_value_of_win_share(raw_nba_payroll, total_wins)
        logger.debug(f"raw_nba_avg_salary_per_ws = {raw_nba_avg_salary_per_ws}, type = {type(raw_nba_avg_salary_per_ws)}")

        nba_avg_salary_per_ws = format_to_dollars(raw_nba_avg_salary_per_ws)
        logger.debug(f"nba_avg_salary_per_ws = {nba_avg_salary_per_ws}, type = {type(nba_avg_salary_per_ws)}")

        nba_avg_salary_per_ws_short = format_to_short_dollar(raw_nba_avg_salary_per_ws)
        logger.debug(f"nba_avg_salary_per_ws_short = {nba_avg_salary_per_ws_short}, type = {type(nba_avg_salary_per_ws_short)}")

        raw_player_salary_per_ws = calc_salary_per_win_share(money_to_float(salary), float(win_shares))
        logger.debug(f"raw_player_salary_per_ws = {raw_player_salary_per_ws}, type = {type(raw_player_salary_per_ws)}")

        player_salary_per_ws = format_to_dollars(raw_player_salary_per_ws)
        logger.debug(f"player_salary_per_ws = {player_salary_per_ws}, type = {type(player_salary_per_ws)}")

        player_salary_per_ws_short = format_to_short_dollar(raw_player_salary_per_ws)
        logger.debug(f"player_salary_per_ws_short = {player_salary_per_ws_short}, type = {type(player_salary_per_ws_short)}")

        # calculate overpay index using raw values
        overpay_index = calc_overpay_index(raw_player_salary_per_ws, raw_nba_avg_salary_per_ws)
        logger.debug(f"overpay_index = {overpay_index}, type = {type(overpay_index)}")

        contract_value_rating = calc_contract_value_rating(overpay_index)
        logger.debug(f"contract_value_rating = {contract_value_rating}, type = {type(contract_value_rating)}")

        contract_value_rating_scaled = f'{int(contract_value_rating * 2)}/10'
        logger.debug(f"contract_value_rating_scaled = {contract_value_rating_scaled}, type = {type(contract_value_rating_scaled)}")

        salary_adjusted = format_to_dollars(calc_adjusted_salary(money_to_float(salary), overpay_index))
        salary_adjusted_short = format_to_short_dollar(money_to_float(salary_adjusted))
        salary_adjusted_pct = str(pct_diff(money_to_float(salary), money_to_float(salary_adjusted))) + '%'
        
        # get per-game stats for display
        pergame_stats = pergame_stats_df.to_dict('records')[0] if not pergame_stats_df.empty else {}
        adv_stats = adv_stats_df.to_dict('records')[0] if not adv_stats_df.empty else {}
        
        return {
            'player_name': player_name,
            'player_id': player_id,
            'age': age,
            'team': team,
            'season': season,
            'year': year,
            'salary': salary,
            'salary_short': salary_short,
            'win_shares': win_shares,
            'salary_cap': salary_cap,
            'salary_cap_short': salary_cap_short,
            'total_teams': total_teams,
            'total_wins': total_wins,
            'nba_payroll': nba_payroll,
            'nba_payroll_short': nba_payroll_short,
            'nba_avg_salary_per_ws': nba_avg_salary_per_ws,
            'nba_avg_salary_per_ws_short': nba_avg_salary_per_ws_short,
            'player_salary_per_ws': player_salary_per_ws,
            'player_salary_per_ws_short': player_salary_per_ws_short,
            'overpay_index': overpay_index,
            'contract_value_rating': contract_value_rating,
            'contract_value_rating_scaled': contract_value_rating_scaled,
            'salary_adjusted': salary_adjusted,
            'salary_adjusted_short': salary_adjusted_short,
            'salary_adjusted_pct': salary_adjusted_pct,
            'pergame_stats': pergame_stats,
            'adv_stats': adv_stats
        }
    except Exception as e:
        logger.error(f"Error analyzing player: {e}")
        raise

@app.route('/get_players')
def get_players():
    try:
        year = season_to_year(request.args.get('season'))

        reg_season_stats_df = extract_table_to_df(f'{year}_reg_season_stats', 'per_game_stats')
        
        # select player_id and player_name, drop duplicates
        season_players = reg_season_stats_df[['player_id', 'player_name']].drop_duplicates()
        
        # sort players alphabetically by name
        season_players = season_players.sort_values('player_name')
        
        # convert to list of dictionaries
        players_list = season_players.to_dict('records')
        
        return jsonify(players_list)
    except Exception as e:

        logger.error(f"Error fetching players: {str(e)}")
        return jsonify([]), 500

@app.route('/', methods=['GET'])
def index():
    """Simple index route that renders the input form"""
    return render_template('index.html', version=version)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Process the form submission and analyze player data"""
    try:
        season = request.form.get('season')
        player_id = request.form.get('player_id')
        
        if not season or not player_id:
            flash('Please enter both a season and a player ID')
            return redirect(url_for('index'))
        
        result = analyze_player(season, player_id)
        
        # Add the helper functions to be available in the template
        result['format_to_short_dollar'] = format_to_short_dollar
        result['money_to_float'] = money_to_float
        
        return render_template('results.html', result=result, version=version)
    except Exception as e:
        flash(f'Error: {str(e)}')
        logger.error(f"Analysis error: {e}", exc_info=True)
        return redirect(url_for('index'))

if __name__ == '__main__':
    # Configure Loguru for file logging
    logger.add("logs/hooperroi_app.log", rotation="500 KB", level="INFO")
    
    # Start the Flask application
    serve(app, host="0.0.0.0", port=8010)