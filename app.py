import time
import pickle
import jsonify
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from datetime import date, datetime
from sklearn.preprocessing import StandardScaler
from flask import Flask, render_template, request

app = Flask(__name__, template_folder = 'templates')
model = pickle.load(open(r'ipl_score_prediction.pkl', 'rb'))

df = pd.read_excel('Fixtures.xlsx')
# year = date.today().year
# month = date.today().month
# day = date.today().day
# if month < 10:
#     month = '0' + str(month)
# if day < 10:
#     day = '0' + str(day)
# today = str(year) + '-' + str(month) + '-' + str(day)
today = '2022-04-02'
text = df[df['DATE'] == today]['MATCH'].values
texts = []
for i in range(len(text)):
    texts.append(str(text[i]))

@app.route('/', methods = ['GET'])

def home():

    return render_template('home.html', len = len(texts), texts = texts)

standard_to = StandardScaler()

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
    innings, overs, score, wickets, last_5_score, last_5_wickets = 0, 0, 0, 0, 0, 0

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
            last_5_score = int(recent.text.split('/')[0].split('\xa0')[-1])
            last_5_wickets = int(recent.text.split('/')[-1].split(' ')[0])
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
            prediction_array = prediction_array + [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif batting_team == 'Delhi Capitals':
            prediction_array = prediction_array + [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        elif batting_team == 'Gujarat Lions':
            prediction_array = prediction_array + [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        elif batting_team == 'Kings XI Punjab':
            prediction_array = prediction_array + [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
        elif batting_team == 'Kolkata Knight Riders':
            prediction_array = prediction_array + [0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
        elif batting_team == 'Mumbai Indians':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        elif batting_team == 'Rajasthan Royals':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
        elif batting_team == 'Rising Pune Supergiant':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
        elif batting_team == 'Royal Challengers Bangalore':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
        elif batting_team == 'Sunrisers Hyderabad':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        
        if bowling_team == 'Chennai Super Kings':
            prediction_array = prediction_array + [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif bowling_team == 'Delhi Capitals':
            prediction_array = prediction_array + [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        elif bowling_team == 'Gujarat Lions':
            prediction_array = prediction_array + [0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        elif bowling_team == 'Kings XI Punjab':
            prediction_array = prediction_array + [0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
        elif bowling_team == 'Kolkata Knight Riders':
            prediction_array = prediction_array + [0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
        elif bowling_team == 'Mumbai Indians':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        elif bowling_team == 'Rajasthan Royals':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
        elif bowling_team == 'Rising Pune Supergiant':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
        elif bowling_team == 'Royal Challengers Bangalore':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
        elif bowling_team == 'Sunrisers Hyderabad':
            prediction_array = prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
                     
        if toss_winner == batting_team:
            prediction_array = prediction_array + [1, 0]
        elif toss_winner == bowling_team:
            prediction_array = prediction_array + [0, 1]
            
        if venue == 'Dr. Y.S. Rajasekhara Reddy ACA-VDCA Cricket Stadium':
            prediction_array + [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        if venue == 'Dubai International Cricket Stadium':
            prediction_array + [0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Eden Gardens':
            prediction_array + [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Feroz Shah Kotla':
            prediction_array + [0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Green Park':
            prediction_array + [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Holkar Cricket Stadium':
            prediction_array + [0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'M Chinnaswamy Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'MA Chidambaram Stadium, Chepauk':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Maharashtra Cricket Association Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Punjab Cricket Association IS Bindra Stadium, Mohali':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]
        elif venue == 'Rajiv Gandhi International Stadium, Uppal':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0]
        elif venue == 'Saurashtra Cricket Association Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0]
        elif venue == 'Sawai Mansingh Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0]
        elif venue == 'Shaheed Veer Narayan Singh International Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]
        elif venue == 'Sharjah Cricket Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0]
        elif venue == 'Sheikh Zayed Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0]
        elif venue == 'Wankhede Stadium':
            prediction_array + [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
        
        entries = prediction_array + [innings, overs, balls, score, wickets, last_5_score, last_5_wickets]
        entries = np.array([entries])
        entries = entries.reshape(1, -1)
        
        prediction = model.predict(entries)[0]
        low = prediction - (0.12 * prediction)
        low = int(np.round(low, 0))
        high = prediction + (0.12 * prediction)
        high = int(np.round(high, 0))
        
        if innings != 0:
            return render_template('predict.html', prediction_text = '{} would be scoring most probably inbetween {} - {}'.format(batting_team, runs, high))
        else:
            return render_template('predict.html', prediction_text = '{}'.format(status))
    else:
        return render_template('home.html')
    
if __name__== '__main__':
    #app.run(host = '0.0.0.0', port = 8080)
    app.run()