import time
import pickle
import jsonify
import requests
import numpy as np
import pandas as pd
from sqlalchemy import *
from bs4 import BeautifulSoup
from datetime import date, datetime
from sklearn.preprocessing import StandardScaler
from flask import Flask, render_template, request
from sqlalchemy.ext.declarative import declarative_base

app = Flask(__name__, template_folder = 'templates')

lr_1 = pickle.load(open(r'linear_1.pkl', 'rb'))
la_1 = pickle.load(open(r'lasso_1.pkl', 'rb'))
ri_1 = pickle.load(open(r'ridge_1.pkl', 'rb'))
abr_1 = pickle.load(open(r'ada_boost_1.pkl', 'rb'))
knr_1 = pickle.load(open(r'k_neighbors_1.pkl', 'rb'))
lr_2 = pickle.load(open(r'logistic_2.pkl', 'rb'))
abc_2 = pickle.load(open(r'ada_boost_2.pkl', 'rb'))

url = 'mysql+mysqlconnector://{user}:{password}@{server}/{database}'.format(user = 'root', password = 'root', server = 'localhost', database = 'ipl')
engine = create_engine(url, echo = True)
base = declarative_base()

df = pd.read_sql_table('fixtures', engine.connect())

year = date.today().year
month = date.today().month
day = date.today().day
if month < 10:
    month = '0' + str(month)
if day < 10:
    day = '0' + str(day)
today = str(year) + '-' + str(month) + '-' + str(day)

text = df[df['DATE'] == today]['MATCH'].values
texts = []
for i in range(len(text)):
    texts.append(str(text[i]))

standard_to = StandardScaler()

@app.route('/', methods = ['GET'])

def home():

    return render_template('home.html', len = len(texts), texts = texts)

@app.route('/analytics', methods = ['GET'])

def analytics():

    return render_template('analytics.html')

@app.route('/predict', methods = ['POST'])


def predict():

    match = request.form['aa']
    url = df[df['MATCH'] == match]['URL'].values[0]
    url = url.split('/')
    url = '/'.join(url[: -1]) + '/'

    teams, toss = [], []
    venue, toss_winner, toss_loser, batting_team, bowling_team, status = '', '', '', '', '', ''
    innings, overs, runs, wickets, runs_last_5_overs, wickets_last_5_overs, playoff, knockout, final = 0, 0, 0, 0, 0, 0, 0, 0, 0

    response = requests.get(url + 'live-cricket-score')
    soup = BeautifulSoup(response.text, 'html.parser')

    #teams

    teams_1 = soup.find_all('div', attrs = {'class' : 'match-header'})
    for team in teams_1:
        teams_2 = team.find_all('p', attrs = {'class' : 'name'})
    teams = [team.text for team in teams_2]

    #innings

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

    #target and overs

    targets = soup.find_all('div', attrs = {'class' : 'match-info match-info-MATCH match-info-MATCH-full-width'})
    try:
        for trgt in targets:
            target_overs = int(trgt.text.split(' ov')[0].split('(')[1].split('/')[1])
            target_runs = int(trgt.text.split('target ')[1].split(')')[0])
    except:
        pass

    response = requests.get(url + 'full-scorecard')
    soup = BeautifulSoup(response.text, 'html.parser')

    #venue

    venue = soup.find('td', attrs = {'class' : 'match-venue'})
    venue = venue.text

    #toss

    try:
        toss_result = soup.find_all('tr')
        toss = [t for t in toss_result if 'Toss' in t.text]
        toss_winner = toss[0].text.split(',')[0].split('Toss')[1]
        toss_loser = [team for team in teams if team != toss_winner]
        toss_loser = toss_loser[0]
    except:
        pass

    #batting and bowling team

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

    #over, score and wickets

    status = soup.find_all('tfoot')
    try:
        if innings == 1:
            overs = float(status[0].text.split(' Ov')[0].split('(')[1])
            score = int(status[0].text.split('/')[0].split(')')[-1])
            if '/' in status[0].text:
                wickets = int(status[0].text.split('/')[1][0])
            else:
                wickets = 10
        else:
            overs = float(status[1].text.split(' Ov')[0].split('(')[1])
            score = int(status[1].text.split('/')[0].split(')')[-1])
            if '/' in status[1].text:
                wickets = int(status[1].text.split('/')[1][0])
            else:
                wickets = 10
        balls = int(np.round((overs % 1) * 10, 0))
        overs = int(overs / 1)
    except:
        pass

    #last five overs

    try:
        if overs >= 5.1:
            recent = soup.find('div', attrs = {'class' : 'recent-overs'})
            runs_last_5_overs = int(recent.text.split('/')[0].split('\xa0')[-1])
            wickets_last_5_overs = int(recent.text.split('/')[-1].split(' ')[0])
        else:
            pass
    except:
        pass

    #status

    status = soup.find_all('div', attrs = {'class' : 'match-header-container'})
    status = status[0].find_all('div', attrs = {'class' : 'status-text'})
    status = status[0].text


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
                     
        if toss_winner == batting_team:
            prediction_array = prediction_array + [1, 0]
        elif toss_winner == bowling_team:
            prediction_array = prediction_array + [0, 1]
            
        if venue == 'Arun_Jaitley_Stadium':
            prediction_array + [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Barabati_Stadium':
            prediction_array + [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Brabourne_Stadium':
            prediction_array + [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Buffalo_Park':
            prediction_array + [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'De_Beers_Diamond_Oval':
            prediction_array + [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Dr_DY_Patil_Sports_Academy':
            prediction_array + [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Dr_YS_Rajasekhara_Reddy_ACA_VDCA_Cricket_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Dubai_International_Cricket_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Eden_Gardens':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Green_Park':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Himachal_Pradesh_Cricket_Association_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Holkar_Cricket_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'JSCA_International_Stadium_Complex':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Kingsmead':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'M_Chinnaswamy_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'MA_Chidambaram_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Maharashtra_Cricket_Association_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Narendra_Modi_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Nehru_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'New_Wanderers_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Newlands':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'OUTsurance_Oval':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Punjab_Cricket_Association_IS_Bindra_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Rajiv_Gandhi_International_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Saurashtra_Cricket_Association_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Sawai_Mansingh_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Shaheed_Veer_Narayan_Singh_International_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
        if venue == 'Sharjah_Cricket_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
        if venue == 'Sheikh_Zayed_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        if venue == 'St_George\'s_Park':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
        if venue == 'SuperSport_Park':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
        if venue == 'Vidarbha_Cricket_Association_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
        if venue == 'Wankhede_Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]

        if innings == 1:
            if (batting_team != 'Lucknow Super Giant') or (batting_team != 'Gujarat Titans') or (bowling_team != 'Lucknow Super Giants') or (bowling_team != 'Gujarat Titans'):
                if overs > 4: 
                    entries = prediction_array + [overs, ball_no, runs, wickets, runs_last_5_overs, wickets_last_5_overs, playoff, knockout, final]
                    entries = np.array([entries])
                    entries = entries.reshape(1, -1)
                    prediction_lr_1 = lr_1.predict(entries)[0]
                    prediction_la_1 = la_1.predict(entries)[0]
                    prediction_ri_1 = ri_1.predict(entries)[0]
                    prediction_abr_1 = abr_1.predict(entries)[0]
                    prediction_knr_1 = knr_1.predict(entries)[0]

                    prediction = (prediction_lr_1 + prediction_la_1 + prediction_ri_1 + prediction_abr_1 + prediction_knr_1) / 5
                    error = 6.580498382

                    low = prediction - error
                    low = int(np.round(low, 0))
                    high = prediction + error
                    high = int(np.round(high, 0))

                    if low < runs:
                        if runs < high:
                            return render_template('predict.html', prediction_text = 'Considering the score and playing conditions at the moment, {} would be scoring most probably inbetween {} - {}'.format(batting_team, runs, high))
                        else:
                            return render_template('predict.html', prediction_text = 'Considering the score and playing conditions at the moment, {} would be scoring most probably inbetween {} - {}'.format(batting_team, runs, int(np.round(runs + error, 0))))
                    else:
                        return render_template('predict.html', prediction_text = 'Considering the score and playing conditions at the moment, {} would be scoring most probably inbetween {} - {}'.format(batting_team, low, high))
                else:
                    return render_template('predict.html', prediction_text = 'Please wait till 5 overs to complete for better result. Thanks for your patience.')
            else:
                return render_template('predict.html', prediction_text = 'Gujarat Titans and Lucknow Super Giant are new to IPL and have no past data point for accurate prediction. Rest assured, we will add these teams in the coming edition. Thank you for understanding.')

        elif innings == 2:
            if (batting_team != 'Lucknow Super Giant') or (batting_team != 'Gujarat Titans') or (bowling_team != 'Lucknow Super Giants') or (bowling_team != 'Gujarat Titans'):
                if overs > 4: 
                    entries = prediction_array + [overs, ball_no, runs, wickets, runs_last_5_overs, wickets_last_5_overs, playoff, knockout, final, target_overs, target_runs]
                    entries = np.array([entries])
                    entries = entries.reshape(1, -1)
                    prediction_lr_2 = lr_2.predict_proba(entries)[0][1]
                    prediction_abc_2 = abc_2.predict_proba(entries)[0][1]

                    prediction = np.round((test['y_test_pred_lr'] + test['y_test_pred_abc']) * 100 / 2, 0)
                    return render_template('predict.html', prediction_text = 'Considering the score and playing conditions at the moment, {} - {}% : {} - {}%'.format(batting_team, prediction, bowling_team, 100 - prediction))
                else:
                    return render_template('predict.html', prediction_text = 'Please wait till 5 overs to complete for better result. Thanks for your patience.')
            else:
                return render_template('predict.html', prediction_text = 'Gujarat Titans and Lucknow Super Giant are new to IPL and have no past data point for accurate prediction. Rest assured, we will add these teams in the coming edition. Thank you for understanding.')
        elif innings == 0:
            return render_template('predict.html', prediction_text = status)

if __name__ == '__main__':
    #app.run(host = '0.0.0.0', port = 8080)
    app.run()