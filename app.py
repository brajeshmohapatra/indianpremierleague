import time
import pickle
import jsonify
import requests
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import *
from bs4 import BeautifulSoup
from datetime import date, datetime
from sklearn.preprocessing import StandardScaler
from flask import Flask, render_template, request
from sqlalchemy.ext.declarative import declarative_base

app = Flask(__name__, template_folder = 'templates')

regressor = pickle.load(open(r'regressor.pkl', 'rb'))
classifier = pickle.load(open(r'classifier.pkl', 'rb'))

standard_to = StandardScaler()

url = 'mysql+mysqlconnector://{user}:{password}@{server}/{database}'.format(user = 'admin', password = 'adminroot', 
                                                                            server = 'indianpremierleague.cloqh08fxh1t.ap-south-1.rds.amazonaws.com',
                                                                            database = 'ipl')
engine = create_engine(url, echo = True)
base = declarative_base()

today = ''

def update_date():

    year = date.today().year
    month = date.today().month
    day = date.today().day
    if month < 10:
        month = '0' + str(month)
    if day < 10:
        day = '0' + str(day)
    today = str(year) + '-' + str(month) + '-' + str(day)
    return today

@app.route('/', methods = ['GET'])

def home():

    fixtures = pd.read_sql_table('fixtures', engine.connect(), columns = ['DATE', 'MATCH'])

    match_list = pd.read_sql_table('match_list', engine.connect(), columns = ['year', 'winner', 'final'])

    match_details = pd.read_sql_table('match_details', engine.connect(), columns = ['batsman', 'bowler', 'batsman_runs', 'is_wicket', 'dismissal_kind'])

    today = update_date()

    text = fixtures[fixtures['DATE'] == today]['MATCH'].values
    texts = []
    for i in range(len(text)):
        texts.append(str(text[i]))

    final_matches = match_list[match_list['final'] == 1]
    most_champion = pd.DataFrame(final_matches['winner'].value_counts())
    most_champion_team = most_champion.index[0]
    most_champion_team_times = most_champion.winner[0]

    current_champion = pd.DataFrame(final_matches[final_matches['year'] == final_matches['year'].max()])
    current_champion_team = current_champion.winner.values[0]
    current_champions_total = pd.DataFrame(final_matches[final_matches['winner'] == current_champion.winner.values[0]])
    current_champions_team_times = current_champions_total.shape[0]

    highest_runs = pd.DataFrame(match_details.groupby('batsman')['batsman_runs'].sum())
    highest_runs = highest_runs.sort_values(by = 'batsman_runs', ascending = False)
    highest_runs_batsman = highest_runs.index[0]
    highest_runs_runs = int(highest_runs.batsman_runs[0])

    highest_wickets = match_details[match_details['is_wicket'] == 1]
    highest_wickets = highest_wickets[~highest_wickets['dismissal_kind'].isin(['run out', 'retired hurt', 'obstructing the field'])]
    highest_wickets = pd.DataFrame(highest_wickets.groupby('bowler')['is_wicket'].sum())
    highest_wickets = highest_wickets.sort_values(by = 'is_wicket', ascending = False)
    highest_wickets_bowler = highest_wickets.index[0]
    highest_wickets_wickets = int(highest_wickets.is_wicket[0])

    return render_template('home.html', len = len(texts), texts = texts, most_champion_team = most_champion_team, most_champion_team_times = most_champion_team_times, current_champion_team = current_champion_team, current_champions_team_times = current_champions_team_times, highest_runs_batsman = highest_runs_batsman, highest_runs_runs = highest_runs_runs, highest_wickets_bowler = highest_wickets_bowler, highest_wickets_wickets = highest_wickets_wickets)

@app.route('/analytics', methods = ['GET'])

def analytics():

    return render_template('analytics.html')

@app.route('/predict', methods = ['POST'])

def predict():

    fixtures = pd.read_sql_table('fixtures', engine.connect(), columns = ['MATCH', 'URL'])

    match = request.form['aa']
    url = fixtures[fixtures['MATCH'] == match]['URL'].values[0]
    url = url.split('/')
    url = '/'.join(url[: -1]) + '/'

    teams, toss = [], []
    venue, toss_winner, toss_loser, batting_team, bowling_team, status = '', '', '', '', '', ''
    innings, overs, runs, wickets, runs_last_5_overs, wickets_last_5_overs, playoff, knockout, final, target_runs, target_overs = 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

    if today == '2022-05-24':
        playoff = 1
        knockout = 0
        final = 0
    elif today == '2022-05-25':
        playoff = 1
        knockout = 1
        final = 0
    elif today == '2022-05-27':
        playoff = 1
        knockout = 1
        final = 0
    elif today == '2022-05-29':
        playoff = 1
        knockout = 1
        final = 1

    response = requests.get(url + 'live-cricket-score')
    soup = BeautifulSoup(response.text, 'html.parser')

    teams_1 = soup.find_all('div', attrs = {'class' : 'match-header'})
    for team in teams_1:
        teams_2 = team.find_all('p', attrs = {'class' : 'name'})
    teams = [team.text for team in teams_2]

    match_status = soup.find_all('div', attrs = {'class' : 'match-info match-info-MATCH match-info-MATCH-full-width'})
    try:
        for ms in match_status:
            verifier = ms.find('div', attrs = {'class' : 'status-text'})
        if 'chose to' in verifier.text:
            innings = 1
        elif 'need' in verifier.text:
            innings = 2
    except:
        pass

    targets = soup.find_all('div', attrs = {'class' : 'match-info match-info-MATCH match-info-MATCH-full-width'})
    try:
        for trgt in targets:
            target_overs = int(trgt.text.split(' ov')[0].split('(')[1].split('/')[1])
            target_runs = int(trgt.text.split('target ')[1].split(')')[0])
    except:
        pass

    response = requests.get(url + 'full-scorecard')
    soup = BeautifulSoup(response.text, 'html.parser')

    venue = soup.find('td', attrs = {'class' : 'match-venue'})
    venue = venue.text

    try:
        toss_result = soup.find_all('tr')
        toss = [t for t in toss_result if 'Toss' in t.text]
        toss_winner = toss[0].text.split(',')[0].split('Toss')[1]
        toss_loser = [team for team in teams if team != toss_winner]
        toss_loser = toss_loser[0]
    except:
        pass

    try:
        if 'bat' in toss[0].text and innings == 1:
            batting_team = toss_winner
            bowling_team = toss_loser
        elif 'bat' in toss[0].text and innings == 2:
            batting_team = toss_loser
            bowling_team = toss_winner
        elif 'field' in toss[0].text and innings == 1:
            batting_team = toss_loser
            bowling_team = toss_winner
        else:
            batting_team = toss_winner
            bowling_team = toss_loser
    except:
        pass

    status = soup.find_all('tfoot')
    try:
        if innings == 1:
            overs = status[0].text.split(' Ov')[0].split('(')[1]
            runs = status[0].text.split('/')[0].split(')')[-1]
            if '/' in status[0].text:
                wickets = int(status[0].text.split('/')[1][0])
            else:
                wickets = 10
        elif innings == 2:
            overs = status[1].text.split(' Ov')[0].split('(')[1]
            runs = status[1].text.split('/')[0].split(')')[-1]
            if '/' in status[1].text:
                wickets = int(status[1].text.split('/')[1][0])
            else:
                wickets = 10

        overs = float(overs)
        balls = int(np.round((overs % 1) * 10, 0))
        overs = int(overs)
        runs = int(runs)
    except:
        pass

    try:
        if overs >= 5.1:
            recent = soup.find('div', attrs = {'class' : 'recent-overs'})
            runs_last_5_overs = int(recent.text.split('/')[0].split('\xa0')[-1])
            wickets_last_5_overs = int(recent.text.split('/')[-1].split(' ')[0])
        else:
            pass
    except:
        pass

    try:
        status = soup.find_all('div', attrs = {'class' : 'match-header-container'})
        status = status[0].find_all('div', attrs = {'class' : 'status-text'})
        status = status[0].text
    except:
        pass


    if request.method == 'POST':
        
        prediction_array = []
        
        if batting_team == 'Chennai Super Kings':
            prediction_array = prediction_array + [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif batting_team == 'Delhi Capitals':
            prediction_array = prediction_array + [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif batting_team == 'Kolkata Knight Riders':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        elif batting_team == 'Mumbai Indians':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
        elif batting_team == 'Punjab Kings':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        elif batting_team == 'Rajasthan Royals':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
        elif batting_team == 'Royal Challengers Bangalore':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
        elif batting_team == 'Sunrisers Hyderabad':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        else:
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        
        if bowling_team == 'Chennai Super Kings':
            prediction_array = prediction_array + [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif bowling_team == 'Delhi Capitals':
            prediction_array = prediction_array + [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif bowling_team == 'Kolkata Knight Riders':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        elif bowling_team == 'Mumbai Indians':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
        elif bowling_team == 'Punjab Kings':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        elif bowling_team == 'Rajasthan Royals':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
        elif bowling_team == 'Royal Challengers Bangalore':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
        elif bowling_team == 'Sunrisers Hyderabad':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        else:
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

                     
        if toss_winner == batting_team:
            prediction_array = prediction_array + [1, 0]
        elif toss_winner == bowling_team:
            prediction_array = prediction_array + [0, 1]

            
        if venue == 'Arun_Jaitley_Stadium':
            prediction_array = prediction_array + [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Barabati_Stadium':
            prediction_array = prediction_array + [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Brabourne Stadium, Mumbai':
            prediction_array = prediction_array + [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Buffalo_Park':
            prediction_array = prediction_array + [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'De_Beers_Diamond_Oval':
            prediction_array = prediction_array + [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Dr DY Patil Sports Academy, Mumbai':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Dr_YS_Rajasekhara_Reddy_ACA_VDCA_Cricket_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Dubai_International_Cricket_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Eden_Gardens':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Green_Park':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Himachal_Pradesh_Cricket_Association_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Holkar_Cricket_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'JSCA_International_Stadium_Complex':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Kingsmead':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'M_Chinnaswamy_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'MA_Chidambaram_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Maharashtra Cricket Association Stadium, Pune':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Narendra_Modi_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Nehru_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'New_Wanderers_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Newlands':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'OUTsurance_Oval':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Punjab_Cricket_Association_IS_Bindra_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Rajiv_Gandhi_International_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Saurashtra_Cricket_Association_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Sawai_Mansingh_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Shaheed_Veer_Narayan_Singh_International_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
        elif venue == 'Sharjah_Cricket_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
        elif venue == 'Sheikh_Zayed_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        elif venue == 'St_George\'s_Park':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
        elif venue == 'SuperSport_Park':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
        elif venue == 'Vidarbha_Cricket_Association_Stadium':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
        elif venue == 'Wankhede Stadium, Mumbai':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        else:
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        if innings == 1:
            balls_remaining = 120 - ((int(overs) * 6) + int(balls))
            if ('Lucknow Super Giants' in teams) or ('Gujarat Titans' in teams):
                return render_template('predict.html', prediction_text = 'Gujarat Titans and Lucknow Super Giants are new to IPL and have no past data for accurate prediction. Rest assured, we will add these teams in the coming edition. Thank you for understanding.', batting_team = batting_team, bowling_team = bowling_team, venue = venue, runs = runs, wickets = wickets, runs_last_5_overs = runs_last_5_overs, wickets_last_5_overs = wickets_last_5_overs, toss_winner = toss_winner, overs = str(overs) + '.' + str(balls), innings = innings)
            else:
                if overs > 4: 
                    entries = prediction_array + [overs, balls, runs, wickets, runs_last_5_overs, wickets_last_5_overs, balls_remaining, playoff, knockout, final]
                    entries = np.array([entries])
                    entries = entries.reshape(1, -1)
                    prediction = int(np.round(regressor.predict(entries)[0], 0))
                    if prediction < 0:
                        prediction = 0

                    return render_template('predict.html', prediction_text = 'Based on the historical data, current score and playing conditions at the moment, {} can score somewhere around {}'.format(batting_team, runs + prediction), batting_team = batting_team, bowling_team = bowling_team, venue = venue, runs = runs, wickets = wickets, runs_last_5_overs = runs_last_5_overs, wickets_last_5_overs = wickets_last_5_overs, toss_winner = toss_winner, overs = str(overs) + '.' + str(balls), innings = innings)
                    
                else:
                    return render_template('predict.html', prediction_text = 'Please wait till 5 overs to complete for better result. Thanks for your patience.', batting_team = batting_team, bowling_team = bowling_team, venue = venue, runs = runs, wickets = wickets, runs_last_5_overs = runs_last_5_overs, wickets_last_5_overs = wickets_last_5_overs, toss_winner = toss_winner, overs = str(overs) + '.' + str(balls), innings = innings)                

        elif innings == 2:
            balls_remaining = (int(target_overs) * 6) - ((int(overs) * 6) + int(balls))
            runs_required = int(target_runs) - int(runs)
            if ('Lucknow Super Giants' in teams) or ('Gujarat Titans' in teams):
                return render_template('predict.html', prediction_text = 'Gujarat Titans and Lucknow Super Giants are new to IPL and have no past data for accurate prediction. Rest assured, we will add these teams in the coming edition. Thank you for understanding.', batting_team = batting_team, bowling_team = bowling_team, venue = venue, runs = runs, wickets = wickets, runs_last_5_overs = runs_last_5_overs, wickets_last_5_overs = wickets_last_5_overs, toss_winner = toss_winner, overs = str(overs) + '.' + str(balls), innings = innings)
            else:
                if overs > 4: 
                    entries = prediction_array + [overs, balls, runs, wickets, runs_last_5_overs, wickets_last_5_overs, target_overs, target_runs, balls_remaining, runs_required, playoff, knockout, final]
                    entries = np.array([entries])
                    entries = entries.reshape(1, -1)
                    prediction = classifier.predict_proba(entries)[0][1]
                    prediction = int(np.round(prediction * 100, 0))

                    color_codes = {'Chennai Super Kings' : '#EBF743', 'Delhi Capitals' : '#43A0F7', 'Gujarat Titans' : '#1C4062', 
               'Kolkata Knight Riders' : '#430F5A', 'Lucknow Super Giants' : '#00FFD0', 'Mumbai Indians' : '#2532C1', 
               'Punjab Kings' : '#E11D1D', 'Rajasthan Royals' : '#FFA3EE', 'Royal Challengers Bangalore' : '#840404', 
               'Sunrisers Hyderabad' : '#FF6600'}

                    teams_playing = [batting_team, bowling_team]
                    percentage = [prediction, 100 - prediction]
                    explode = (0.01, 0.01)
                    colors = [color_codes[key] for key in color_codes if key in teams_playing]

                    plt.pie(percentage, labels = teams, colors = colors, autopct = '%1.0f%%', pctdistance = 1.5, explode = explode)
                    centre_circle = plt.Circle((0, 0), 0.60, fc = 'white')
                    fig = plt.gcf()
                    fig.gca().add_artist(centre_circle)
                    fig.savefig('static/result.jpg')
                    return render_template('predict.html', prediction_text = 'Based on the historical data, current score and playing conditions at the moment', batting_team = batting_team, bowling_team = bowling_team, venue = venue, runs = runs, wickets = wickets, runs_last_5_overs = runs_last_5_overs, wickets_last_5_overs = wickets_last_5_overs, toss_winner = toss_winner, overs = str(overs) + '.' + str(balls), innings = innings)
                else:
                    return render_template('predict.html', prediction_text = 'Please wait till 5 overs to complete for better result. Thanks for your patience.', batting_team = batting_team, bowling_team = bowling_team, venue = venue, runs = runs, wickets = wickets, runs_last_5_overs = runs_last_5_overs, wickets_last_5_overs = wickets_last_5_overs, toss_winner = toss_winner, overs = str(overs) + '.' + str(balls), innings = innings)                

        elif innings == 0:
            fig = plt.figure(figsize=(0.1, 0.1))
            fig.savefig('static/result.jpg')
            return render_template('predict.html', prediction_text = status)

    else:
        return render_template('home.html', len = len(texts), texts = texts, most_champion_team = most_champion_team, most_champion_team_times = most_champion_team_times, current_champion_team = current_champion_team, current_champions_team_times = current_champions_team_times, highest_runs_batsman = highest_runs_batsman, highest_runs_runs = highest_runs_runs, highest_wickets_bowler = highest_wickets_bowler, highest_wickets_wickets = highest_wickets_wickets)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 8080)
    # app.run()