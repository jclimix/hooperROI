from flask import Flask, render_template, request, redirect, url_for, send_from_directory
import pandas as pd
import numpy as np
import os
from scrapePlayerPage import *
from playerSalaryData import *
from loguru import logger

app = Flask(__name__)

logger.add("app.log", rotation="10MB", retention="10 days", level="INFO")

# folder where CSV files are stored
CSV_FOLDER = os.path.join(os.getcwd(), "static", "data")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data/<filename>')
def get_csv(filename):
    return send_from_directory(CSV_FOLDER, filename)

@app.route('/search', methods=['POST'])
def search_player():
    player_name = request.form['player']
    season = request.form['season']

    if not player_name or not season:
        logger.warning("Player name or season is missing. Redirecting to index.")
        return redirect(url_for('index'))  # should redirect if fields are empty

    logger.info(f"Searching for player: {player_name}, Season: {season}")

    # season to numeric year
    year = convert_nba_season_to_year(season)
    player_id = get_player_id(year, player_name)

    if player_id == "Player not found":
        logger.error("Player not found. Returning error message.")
        return render_template('results.html', error="Player not found. Try again.")

    soup_data = scrape_html(player_id)
    player_headshot = get_player_headshot(soup_data, player_id)

    # scrape per-game stats
    pergame_table = scrape_html_table(soup_data, table_id="per_game_stats")
    pergame_table_df = html_table_to_df_stats(pergame_table)
    
    try:
        age = pergame_table_df.loc[pergame_table_df['Season'] == season, 'Age'].values[0]
        position = pergame_table_df.loc[pergame_table_df['Season'] == season, 'Pos'].values

        if isinstance(position, (list, tuple, np.ndarray)) and len(position) > 0:
            position = position[0]  # get first row
            if isinstance(position, (list, tuple, np.ndarray)) and len(position) > 0:
                position = position[0]  # get first valid value from row

        team = pergame_table_df.loc[pergame_table_df['Season'] == season, 'Team'].values[-1]
    except Exception as e:
        logger.error(f"Error extracting player details: {e}")
        age, position, team = "N/A", "N/A", "N/A"

    pergame_table_df = rearrange_base_stats_df(pergame_table_df)

    # scrape advanced stats
    adv_table = scrape_html_table(soup_data, table_id="advanced")
    adv_table_df = html_table_to_df_stats(adv_table)
    adv_table_df = rearrange_adv_stats_df(adv_table_df)

    pergame_table_df = clean_duplicate_columns(pergame_table_df)
    adv_table_df = clean_duplicate_columns(adv_table_df)

    salary_analysis_df = create_player_salary_analysis_df(soup_data, season)
    
    try:
        contract_value_rating = salary_analysis_df.loc[salary_analysis_df['Season'] == season, 'Contract Value Rating'].values[0]
        salary = salary_analysis_df.loc[salary_analysis_df['Season'] == season, 'Salary'].values[0]
        salary_per_ws = salary_analysis_df.loc[salary_analysis_df['Season'] == season, 'Salary Per WS'].values[0]
        
        logger.info(f"Salary Per WS: {salary_per_ws}, Salary: {salary}")
        logger.info(f"CVR: {contract_value_rating}, Salary: {salary}")
    except Exception as e:
        logger.error(f"Error extracting salary data: {e}")
        contract_value_rating, salary = "N/A", "N/A"

    # dfs to HTML tables
    pergame_html = pergame_table_df.to_html(classes="table table-striped", index=False)
    adv_stats_html = adv_table_df.to_html(classes="table table-striped", index=False)
    salary_analysis_html = salary_analysis_df.to_html(classes="table table-striped", index=False)

    return render_template(
        'results.html',
        player_name=player_name,
        player_id=player_id,
        player_headshot=player_headshot,
        season=season,
        age=age,
        position=position,
        team=team,
        url=f"https://www.basketball-reference.com/players/{player_id[0]}/{player_id}.html",
        pergame_html=pergame_html,
        adv_stats_html=adv_stats_html,
        salary_analysis_html=salary_analysis_html,
        contract_value_rating=contract_value_rating,
        salary=salary
    )

if __name__ == '__main__':
    logger.info("Starting Flask app...")
    app.run(host="0.0.0.0", port=8010)
