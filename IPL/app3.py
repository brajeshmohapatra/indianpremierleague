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

def team_initialize(team):

    teams = {'Chennai Super Kings' : 0, 'Deccan Chargers' : 0, 'Delhi Capitals' : 0, 'Gujarat Lions' : 0, 
             'Kochi Tuskers Kerala' : 0, 'Kolkata Knight Riders' : 0, 'Mumbai Indians' : 0, 'Pune Warriors' : 0, 
             'Punjab Kings' : 0, 'Rajasthan Royals' : 0, 'Rising Pune Supergiant' : 0, 'Royal Challengers Bangalore' : 0, 
             'Sunrisers Hyderabad' : 0}
    if team in teams.keys():
        teams[team] = 1
    teams_list = list(teams.values())
    return teams_list

def venue_initialize(venue):

    venues = {'Arun Jaitley Stadium' : 0, 'Barabati Stadium' : 0, 'Brabourne Stadium, Mumbai' : 0, 'Buffalo Park' : 0, 
              'De Beers Diamond Oval' : 0, 'Dr DY Patil Sports Academy' : 0, 
              'Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium' : 0, 'Dubai International Cricket Stadium' : 0, 
              'Eden Gardens' : 0, 'Green Park' : 0, 'Himachal Pradesh Cricket Association Stadium' : 0, 
              'Holkar Cricket Stadium' : 0, 'JSCA International Stadium Complex' : 0, 'Kingsmead' : 0, 
              'M Chinnaswamy Stadium' : 0, 'MA Chidambaram Stadium' : 0, 'Maharashtra Cricket Association Stadium, Pune' : 0, 
              'Narendra Modi Stadium' : 0, 'Nehru Stadium' : 0, 'New Wanderers Stadium' : 0, 'Newlands' : 0, 
              'OUTsurance Oval' : 0, 'Punjab Cricket Association IS Bindra Stadium' : 0, 
              'Rajiv Gandhi International Stadium' : 0, 'Saurashtra Cricket Association Stadium' : 0, 
              'Sawai Mansingh Stadium' : 0, 'Shaheed Veer Narayan Singh International Stadium' : 0, 
              'Sharjah Cricket Stadium' : 0, 'Sheikh Zayed Stadium' : 0, 'St George\'s Park' : 0, 'SuperSport Park' : 0, 
              'Vidarbha Cricket Association Stadium' : 0, 'Wankhede Stadium, Mumbai' : 0}
    if venue in venues.keys():
        venues[venue] = 1
    venues_list = list(venues.values())
    return venues_list


def toss_initialize(toss_winner, batting_team, bowling_team):

    if toss_winner == batting_team:
        toss_list = [1, 0]
    elif toss_winner == bowling_team:
        toss_list = [0, 1]
    return toss_list

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

    fixtures = pd.read_sql_table('fixtures', engine.connect(), columns = ['HOME TEAM', 'AWAY TEAM', 'MATCH', 'VENUE', 'URL'])

    match = request.form['aa']
    url = fixtures[fixtures['MATCH'] == match]['URL'].values[0]
    url = url.split('/')
    url = '/'.join(url[: -1]) + '/'
    teams = [fixtures[fixtures['MATCH'] == match]['HOME TEAM'].values[0], fixtures[fixtures['MATCH'] == match]['AWAY TEAM'].values[0]]
    venue = fixtures[fixtures['MATCH'] == match]['VENUE'].values[0]
    print('teams: ', teams)
    print('venue: ', venue)

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
    else:
        playoff = 0
        knockout = 0
        final = 0

    response = requests.get(url + 'live-cricket-score')
    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        status = soup.find_all('p', attrs = {'class' : 'ds-text-tight-m ds-font-regular ds-truncate ds-text-typo-title'})
        status = status[0].text
    except:
        status = 'Please stay tuned.'
    print('status :', status)

    if 'chose to' in status:
        innings = 1
    elif 'need' in status:
        innings = 2
    else:
        innings = 0
    print('innings: ', innings)

    try:
        targets = soup.find_all('span', attrs = {'class' : 'ds-text-compact-s ds-mr-0.5'})
        targets = [trgt.text for trgt in targets if 'target' in trgt.text]
        target_runs = int(targets[0].split(')')[0].split('target ')[-1])
        target_overs = float(targets[0].split('(')[-1].split(' ov')[0].split('/')[-1])
    except:
        target_runs = 0
        target_overs = 0
    print('target_runs: ', target_runs)
    print('target_overs: ', target_overs)

    score_wickets = soup.find_all('div', attrs = {'class' : 'ds-text-compact-m ds-text-typo-title'})
    score_wickets = [sw.text for sw in score_wickets]
    if innings == 1:
        runs = int(score_wickets[0].split(') ')[-1].split('/')[0])
        if '/' in score_wickets[0]:
            wickets = int(score_wickets[0].split(') ')[-1].split('/')[1])
        else:
            wickets = 10
    elif innings == 2:
        runs = int(score_wickets[1].split(') ')[-1].split('/')[0])
        if '/' in score_wickets[1]:
            wickets = int(score_wickets[1].split(') ')[-1].split('/')[1])
        else:
            wickets = 10
    else:
        runs = 0
        wickets = 0

    print('runs: ', runs)
    print('wickets: ', wickets)

    response = requests.get(url + 'full-scorecard')
    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        toss_result = soup.find_all('span', attrs = {'class' : 'ds-text-tight-s ds-font-regular'})
        toss = [tr.text for tr in toss_result if ', elected' in tr.text]
        toss_winner = toss[0].split(',')[0]
        toss_loser = [team for team in teams if team != toss_winner]
        toss_loser = toss_loser[0]
    except:
        toss_winner = ''
        toss_loser = ''
    print('toss_winner: ', toss_winner)
    print('toss_loser: ', toss_loser)

    try:
        if 'bat' in toss[0] and innings == 1:
            batting_team = toss_winner
            bowling_team = toss_loser
        elif 'bat' in toss[0] and innings == 2:
            batting_team = toss_loser
            bowling_team = toss_winner
        elif 'field' in toss[0] and innings == 1:
            batting_team = toss_loser
            bowling_team = toss_winner
        else:
            batting_team = toss_winner
            bowling_team = toss_loser
    except:
        batting_team = ''
        bowling_team = ''
    print('batting_team: ', batting_team)
    print('bowling_team: ', bowling_team)

    overs_data = soup.find_all('tr', attrs = {'class' : 'ds-border-b ds-border-line ds-font-bold ds-bg-fill-content-alternate ds-text-tight-m'})
    overs_data = [sc.text for sc in overs_data]
    print('overs_data:', overs_data)
    try:
        if innings == 1:
            overs = float(overs_data[0].split('TOTAL')[-1].split(' Ov')[0])
        elif innings == 2:
            overs = float(overs_data[1].split('TOTAL')[-1].split(' Ov')[0])

        overs = float(overs)
        balls = int(np.round((overs % 1) * 10, 0))
        overs = int(overs)
        runs = int(runs)
    except:
        overs = 0
        balls = 0
        runs = 0
        wickets = 0
    print('overs: ', overs)
    print('balls: ', balls)

    try:
        if overs >= 5.1:
            recent = soup.find_all('div', attrs = {'class' : 'ds-text-tight-s ds-font-regular ds-overflow-x-auto ds-scrollbar-hide ds-whitespace-nowrap ds-mt-1 md:ds-mt-0 lg:ds-flex lg:ds-items-center lg:ds-justify-between lg:ds-px-4 lg:ds-py-2 lg:ds-bg-fill-content-alternate ds-text-ui-typo-mid md:ds-text-typo-paragraph'})
            recent = recent[0].text
            runs_last_5_overs = int(recent.split('/')[0].split('\xa0')[-1])
            wickets_last_5_overs = int(recent.split('/')[-1].split(' ')[0])
        else:
            runs_last_5_overs = 0
            wickets_last_5_overs = 0
    except:
        runs_last_5_overs = 0
        wickets_last_5_overs = 0
    print('runs_last_5_overs: ', runs_last_5_overs)
    print('wickets_last_5_overs:', wickets_last_5_overs)

    if request.method == 'POST':
        
        prediction_array = []
        
        prediction_array = prediction_array + team_initialize(batting_team) + team_initialize(bowling_team) + toss_initialize(toss_winner, batting_team, bowling_team) + venue_initialize(venue)

        if innings == 1:
            balls_remaining = 120 - ((int(overs) * 6) + int(balls))
            print('balls_remaining: ', balls_remaining)
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
            print('balls_remaining :', balls_remaining)
            print('runs_required :', runs_required)
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

                    plt.figure()
                    plt.pie(percentage, labels = teams, colors = colors, autopct = '%1.0f%%', pctdistance = 0.70, textprops = {'fontsize' : 8})
                    centre_circle = plt.Circle((0, 0), 0.50, fc = 'white')
                    fig = plt.gcf()
                    fig.gca().add_artist(centre_circle)
                    fig.savefig('static/result.png')
                    plt.clf()
                    return render_template('predict.html', prediction_text = 'Based on the historical data, current score and playing conditions at the moment', batting_team = batting_team, bowling_team = bowling_team, venue = venue, runs = runs, wickets = wickets, runs_last_5_overs = runs_last_5_overs, wickets_last_5_overs = wickets_last_5_overs, toss_winner = toss_winner, overs = str(overs) + '.' + str(balls), innings = innings)
                else:
                    return render_template('predict.html', prediction_text = 'Please wait till 5 overs to complete for better result. Thanks for your patience.', batting_team = batting_team, bowling_team = bowling_team, venue = venue, runs = runs, wickets = wickets, runs_last_5_overs = runs_last_5_overs, wickets_last_5_overs = wickets_last_5_overs, toss_winner = toss_winner, overs = str(overs) + '.' + str(balls), innings = innings)                

        elif innings == 0:
            fig = plt.figure(figsize = (0.1, 0.1))
            fig.savefig('static/result.jpg')
            return render_template('predict.html', prediction_text = status)

    else:
        return render_template('home.html', len = len(texts), texts = texts, most_champion_team = most_champion_team, most_champion_team_times = most_champion_team_times, current_champion_team = current_champion_team, current_champions_team_times = current_champions_team_times, highest_runs_batsman = highest_runs_batsman, highest_runs_runs = highest_runs_runs, highest_wickets_bowler = highest_wickets_bowler, highest_wickets_wickets = highest_wickets_wickets)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 8080)
    # app.run()