import os
import json
import zipfile
import requests
import warnings
import numpy as np
import pandas as pd
from sqlalchemy import *
from datetime import date, datetime
from IPython.display import display, HTML
from sqlalchemy.ext.declarative import declarative_base
warnings.filterwarnings('ignore')
pd.pandas.set_option('display.max_rows', None)
pd.pandas.set_option('display.max_columns', None)
display(HTML('<style>.container{width : 100% ! important;}</style>'))

missed_matches = pd.read_excel('Missed Matches.xlsx')

url = 'mysql+mysqlconnector://{user}:{password}@{server}/{database}'.format(user = 'admin', password = 'adminroot', 
                                                                            server = 'indianpremierleague.cloqh08fxh1t.ap-south-1.rds.amazonaws.com',
                                                                            database = 'ipl')
engine = create_engine(url, echo = True)
base = declarative_base()

url = 'https://cricsheet.org/downloads/ipl_json.zip'
r = requests.get(url, allow_redirects = True)
open('ipl.zip', 'wb').write(r.content)
print('Data downloaded.')

with zipfile.ZipFile('ipl.zip', 'r') as zip_ref:
    zip_ref.extractall('Matches Extracted')
print('Data extracted.')

old = os.listdir('Matches')
new = os.listdir('Matches Extracted')
new = [file for file in new if file not in old]

for file in new:
    os.replace('Matches Extracted\\' + file, 'Matches New\\' + file)
print('Files moved to Matches New folder.')
    
files = os.listdir('Matches New\\')

match_id, city, date, player_of_match, venue, team1, team2, toss_winner = [], [], [], [], [], [], [], []
toss_decision, winner, result, result_margin, method, players, umpire1, umpire2 = [], [], [], [], [], [], [], []

for file in files:
    if '.json' in file:
        match = open('Matches New\\' + str(file))        
        data = json.load(match)
        match_id.append(match.name.split('\\')[-1].split('.')[0])
        try:
            city.append(data['info']['city'])
        except:
            city.append(np.nan)
        date.append(data['info']['dates'][0])
        try:
            player_of_match.append(data['info']['player_of_match'][0])
        except:
            player_of_match.append(np.nan)
        venue.append(data['info']['venue'])
        team1.append(data['info']['teams'][0])
        team2.append(data['info']['teams'][1])
        try:
            toss_winner.append(data['info']['toss']['winner'])
        except:
            toss_winner.append(np.nan)
        try:
            toss_decision.append(data['info']['toss']['decision'])
        except:
            toss_decision.append(np.nan)
        try:
            winner.append(data['info']['outcome']['winner'])
        except:
            winner.append(np.nan)
        try:
            result.append([key for key in data['info']['outcome']['by'].items()][0][0])
        except:
            result.append(np.nan)
        try:
            result_margin.append(data['info']['outcome']['by']['runs'])
        except:
            try:
                result_margin.append(data['info']['outcome']['by']['wickets'])
            except:
                result_margin.append(np.nan)
        try:
            method.append(data['info']['outcome']['method'])
        except:
            method.append(np.nan)
        match.close()
        players_list = data['info']['players'][data['info']['teams'][0]] + data['info']['players'][data['info']['teams'][1]]
        players_list = ', '.join(players_list)
        players.append(players_list)
        umpire1.append(data['info']['officials']['umpires'][0])
        umpire2.append(data['info']['officials']['umpires'][1])        
df = pd.DataFrame({'match_id' : match_id, 'city' : city, 'date' : date, 'player_of_match' : player_of_match, 'venue' : venue, 
                   'team1' : team1, 'team2' : team2, 'toss_winner' : toss_winner, 'toss_decision' : toss_decision, 
                   'winner' : winner, 'result' : result, 'result_margin' : result_margin, 'method' : method, 
                   'players' : players, 'umpire1' : umpire1, 'umpire2' : umpire2})
df['match_id'] = df['match_id'].astype('int64')
df['date'] = pd.to_datetime(df['date'])
# df = pd.concat([df, missed_matches], axis = 0)
df['year'] = pd.DatetimeIndex(df['date']).year
df.sort_values(by = 'match_id', ascending = True, inplace = True)
df = df[['match_id', 'year', 'city', 'date', 'player_of_match', 'venue', 'team1', 'team2', 'toss_winner', 'toss_decision', 'winner', 'result', 
         'result_margin', 'method', 'players', 'umpire1', 'umpire2']]
df.reset_index(inplace = True, drop = True)
matches = pd.DataFrame()
for yr in df.year.unique():
    tdf = df[df['year'] == yr]
    tdf['playoff'] = 0
    tdf['knockout'] = 0
    tdf['final'] = 0
    if yr != 2022:
        if yr <= 2009:
            tdf['playoff'][tdf.index.max()] = 1
            tdf['playoff'][tdf.index.max() - 1] = 1
            tdf['playoff'][tdf.index.max() - 2] = 1
        else:
            tdf['playoff'][tdf.index.max()] = 1
            tdf['playoff'][tdf.index.max() - 1] = 1
            tdf['playoff'][tdf.index.max() - 2] = 1
            tdf['playoff'][tdf.index.max() - 3] = 1
        if yr == 2010:
            tdf['knockout'][tdf.index.max()] = 1
            tdf['knockout'][tdf.index.max() - 1] = 1
            tdf['knockout'][tdf.index.max() - 2] = 1
            tdf['knockout'][tdf.index.max() - 3] = 1
        else:
            tdf['knockout'][tdf.index.max()] = 1
            tdf['knockout'][tdf.index.max() - 1] = 1
            tdf['knockout'][tdf.index.max() - 2] = 1
        tdf['final'][tdf.index.max()] = 1
        matches = pd.concat([matches, tdf], axis = 0)
    else:
        matches = pd.concat([matches, tdf], axis = 0)
print('Matches created.')

match_id, innings, overs, balls, batsman, non_striker, bowler, batsman_runs = [], [], [], [], [], [], [], []
extra_runs, total_runs, non_boundary, is_wicket, dismissal_kind, player_dismissed, fielder_1, fielder_2 = [], [], [], [], [], [], [], []
fielder_3, extras_type_1, extras_type_2, batting_team, bowling_team, target_overs, target_runs = [], [], [], [], [], [], []

for file in files:
    if '.json' in file:
        match = open('Matches New\\' + str(file))
        
        data = json.load(match)
        for inn in range(2):
            for ov in range(20):
                for ball in range(10):                      
                    match_id.append(match.name.split('\\')[-1].split('.')[0])
                    innings.append(inn + 1)
                    overs.append(ov)
                    balls.append(ball + 1)
                    try:
                        batsman.append(data['innings'][inn]['overs'][ov]['deliveries'][ball]['batter'])
                    except:
                        batsman.append(np.nan)
                    try:
                        non_striker.append(data['innings'][inn]['overs'][ov]['deliveries'][ball]['non_striker'])
                    except:
                        non_striker.append(np.nan)
                    try:
                        bowler.append(data['innings'][inn]['overs'][ov]['deliveries'][ball]['bowler'])
                    except:
                        bowler.append(np.nan)
                    try:
                        batsman_runs.append(data['innings'][inn]['overs'][ov]['deliveries'][ball]['runs']['batter'])
                    except:
                        batsman_runs.append(np.nan)
                    try:
                        extra_runs.append(data['innings'][inn]['overs'][ov]['deliveries'][ball]['runs']['extras'])
                    except:
                        extra_runs.append(np.nan)
                    try:
                        total_runs.append(data['innings'][inn]['overs'][ov]['deliveries'][ball]['runs']['total'])
                    except:
                        total_runs.append(np.nan)
                    try:
                        non_boundary.append(data['innings'][inn]['overs'][ov]['deliveries'][ball]['runs']['non_boundary'])
                    except:
                        non_boundary.append(np.nan)
                    try:
                        dismissal_kind.append(data['innings'][inn]['overs'][ov]['deliveries'][ball]['wickets'][0]['kind'])
                    except:
                        dismissal_kind.append('')
                    try:
                        player_dismissed.append(data['innings'][inn]['overs'][ov]['deliveries'][ball]['wickets'][0]['player_out'])
                    except:
                        player_dismissed.append(np.nan)
                    try:
                        fielder_1.append(data['innings'][inn]['overs'][ov]['deliveries'][ball]['wickets'][0]['fielders'][0]['name'])
                    except:
                        fielder_1.append('')
                    try:
                        fielder_2.append(data['innings'][inn]['overs'][ov]['deliveries'][ball]['wickets'][0]['fielders'][1]['name'])
                    except:
                        fielder_2.append('')
                    try:
                        fielder_3.append(data['innings'][inn]['overs'][ov]['deliveries'][ball]['wickets'][0]['fielders'][2]['name'])
                    except:
                        fielder_3.append('')
                    try:
                        extras_type_1.append(
                            [key for key in data['innings'][inn]['overs'][ov]['deliveries'][ball]['extras'].items()][0][0])
                    except:
                        extras_type_1.append('')
                    try:
                        extras_type_2.append(
                            [key for key in data['innings'][inn]['overs'][ov]['deliveries'][ball]['extras'].items()][1][0])
                    except:
                        extras_type_2.append('')
                    try:
                        batting_team.append(data['innings'][inn]['team'])
                    except:
                        batting_team.append(np.nan)
                    try:
                        bowling_team.append([team for team in data['info']['teams'] if team != data['innings'][inn]['team']][0])
                    except:
                        bowling_team.append(np.nan)
                    try:
                        target_overs.append(data['innings'][inn]['target']['overs'])
                    except:
                        target_overs.append(np.nan)
                    try:
                        target_runs.append(data['innings'][inn]['target']['runs'])
                    except:
                        target_runs.append(np.nan)        
        match.close()
details = pd.DataFrame({'match_id' : match_id, 'innings' : innings, 'overs' : overs, 'balls' : balls, 'batsman' : batsman, 
                   'non_striker' : non_striker, 'bowler' : bowler, 'batsman_runs' : batsman_runs, 'extra_runs' : extra_runs, 
                   'total_runs' : total_runs, 'non_boundary' : non_boundary, 'dismissal_kind' : dismissal_kind, 
                   'player_dismissed' : player_dismissed, 'fielder1' : fielder_1, 'fielder2' : fielder_2, 'fielder3' : fielder_3, 
                   'extras_type1' : extras_type_1, 'extras_type2' : extras_type_2, 'batting_team' : batting_team, 
                   'bowling_team' : bowling_team, 'target_overs' : target_overs, 'target_runs' : target_runs})
details = details[details['batsman'].isna() == False]
details.reset_index(inplace = True, drop = True)
fielder, fielder_temp = [], []
for i in details.index:
    fielder_list = []
    for col in ['fielder1', 'fielder2', 'fielder3']:
        if details[col][i] != '':
            fielder_list.append(details[col][i])
    fielder_temp.append(', '.join(fielder_list))
for i in fielder_temp:
    if i != '':
        fielder.append(i)
    else:
        fielder.append(np.nan)
details['fielder'] = fielder
details.drop(['fielder1', 'fielder2', 'fielder3'], axis = 1, inplace = True)
extras_type, extras_type_temp = [], []
for i in details.index:
    extras_list = []
    for col in ['extras_type1', 'extras_type2']:
        if details[col][i] != '':
            extras_list.append(details[col][i])
    extras_type_temp.append(', '.join(extras_list))
for i in extras_type_temp:
    if i != '':
        extras_type.append(i)
    else:
        extras_type.append(np.nan)
details['extras_type'] = extras_type
details.drop(['extras_type1', 'extras_type2'], axis = 1, inplace = True)
for i in details.index:
    if details['dismissal_kind'][i] != '':
        is_wicket.append(1)
    else:
        is_wicket.append(0)
details['is_wicket'] = is_wicket
dk = []
for i in details.index:
    if details['dismissal_kind'][i] != '':
        dk.append(details['dismissal_kind'][i])
    else:
        dk.append(np.nan)
details['dismissal_kind'] = dk
nb = []
for i in details.index:
    if details['non_boundary'][i] == 'True':
        nb.append(1)
    else:
        nb.append(0)
details['non_boundary'] = nb 
details['match_id'] = details['match_id'].astype('int64')
details = details[['match_id', 'innings', 'overs', 'balls', 'batsman', 'non_striker', 'bowler', 'batsman_runs', 'extra_runs', 'total_runs', 
         'non_boundary', 'is_wicket', 'dismissal_kind', 'player_dismissed', 'fielder', 'extras_type', 'batting_team', 'bowling_team', 
         'target_overs', 'target_runs']]
print('Match Details created.')

ipl = details.merge(matches, on = 'match_id', how = 'left')
ipl['date'] = ipl['date'].astype(str)
ipl['year'] = ipl['date'].apply(lambda dateString : datetime.strptime(dateString,'%Y-%m-%d').year)
ipl['date'] = pd.to_datetime(ipl['date'])
ipl = ipl.sort_values(by = ['match_id', 'innings', 'overs', 'balls'])
ipl.reset_index(inplace = True, drop = True)
print('IPL dataset formed.')

final_score = pd.DataFrame(ipl.groupby(['match_id', 'innings'])['total_runs'].sum())
final_score.reset_index(inplace = True)
final_score.rename(columns = {'total_runs' : 'final_score'}, inplace = True)
ipl = ipl.merge(final_score, on = ['match_id', 'innings'], how = 'left')
print('final_score column completed.')

total_wickets = pd.DataFrame(ipl.groupby(['match_id', 'innings'])['is_wicket'].sum())
total_wickets.reset_index(inplace = True)
total_wickets.rename(columns = {'is_wicket' : 'total_wickets'}, inplace = True)
ipl = ipl.merge(total_wickets, on = ['match_id', 'innings'], how = 'left')
print('total_wickets column completed.')

ipl['runs'] = 0
ipl['runs'][0] = ipl['total_runs'][0]
ipl['runs'][ipl.shape[0]-1] = ipl['final_score'][ipl.shape[0]-1]
for i in range(1, ipl.shape[0]-1):
    if ipl['match_id'][i] == ipl['match_id'][i+1]:
        if ipl['innings'][i] == ipl['innings'][i+1]:
            ipl['runs'][i] = ipl['total_runs'][i] + ipl['runs'][i-1]
for i in range(1, ipl.shape[0]-1):
    if ipl['match_id'][i] != ipl['match_id'][i+1]:
        ipl['runs'][i] = ipl['total_runs'][i] + ipl['runs'][i-1]
for i in range(1, ipl.shape[0]-1):
    if ipl['match_id'][i] == ipl['match_id'][i+1]:
        if ipl['innings'][i] != ipl['innings'][i+1]:
            ipl['runs'][i] = ipl['total_runs'][i] + ipl['runs'][i-1]
print('runs column completed.')
            
ipl['wickets'] = 0
ipl['wickets'][0] = ipl['is_wicket'][0]
ipl['wickets'][ipl.shape[0]-1] = ipl['total_wickets'][ipl.shape[0]-1]
for i in range(1, ipl.shape[0]-1):
    if ipl['match_id'][i] == ipl['match_id'][i+1]:
        if ipl['innings'][i] == ipl['innings'][i+1]:
            ipl['wickets'][i] = ipl['is_wicket'][i] + ipl['wickets'][i-1]
for i in range(ipl.shape[0]-1):
    if ipl['match_id'][i] != ipl['match_id'][i+1]:
        ipl['wickets'][i] = ipl['total_wickets'][i]
for i in range(ipl.shape[0]-1):
    if ipl['match_id'][i] == ipl['match_id'][i+1]:
        if ipl['innings'][i] != ipl['innings'][i+1]:
            ipl['wickets'][i] = ipl['total_wickets'][i]
print('wickets column completed.')
            
ipl['runs_last_5_overs'] = 0
for i in ipl.index:
    if ipl['overs'][i] <= 4:
        ipl['runs_last_5_overs'][i] = ipl['runs'][i]
for i in ipl.index:
    if ipl['overs'][i] > 4:
        if ipl['match_id'][i] == ipl['match_id'][i-30]:
            if ipl['innings'][i] == ipl['innings'][i-30]:
                ipl['runs_last_5_overs'][i] = ipl['runs'][i] - ipl['runs'][i-30]
print('runs_last_5_overs column completed.')
                
ipl['wickets_last_5_overs'] = 0
for i in ipl.index:
    if ipl['overs'][i] <= 4:
        ipl['wickets_last_5_overs'][i] = ipl['wickets'][i]
for i in ipl.index:
    if ipl['overs'][i] > 4:
        if ipl['match_id'][i] == ipl['match_id'][i-30]:
            if ipl['innings'][i] == ipl['innings'][i-30]:
                ipl['wickets_last_5_overs'][i] = ipl['wickets'][i] - ipl['wickets'][i-30]
for i in ipl.index:
    if ipl['overs'][i] > 4:
        if ipl['match_id'][i] != ipl['match_id'][i-1]:
            ipl['wickets_last_5_overs'][i-1] = ipl['wickets'][i-1] - ipl['wickets'][i-31]
for i in ipl.index:
    if ipl['overs'][i] > 4:
        if ipl['match_id'][i] == ipl['match_id'][i-1]:
            if ipl['innings'][i] != ipl['innings'][i-1]:
                ipl['wickets_last_5_overs'][i-1] = ipl['wickets'][i-1] - ipl['wickets'][i-31]
print('wickets_last_5_overs column completed.')

ipl['ball_no'] = 0
ipl['extras_type'] = ipl['extras_type'].astype(str)
for i in ipl.index:
    if (ipl['overs'][i] == 0) & (ipl['balls'][i] == 1):
        ipl['ball_no'][i] = 1
for i in range(1, ipl.shape[0]):
    if (ipl['overs'][i] == 0) & (ipl['balls'][i] == 1):
        pass
    else:
        if 'wides' in ipl['extras_type'][i-1]:
            ipl['ball_no'][i] = ipl['ball_no'][i-1]
        elif 'noballs' in ipl['extras_type'][i-1]:
            ipl['ball_no'][i] = ipl['ball_no'][i-1]
        else:
            ipl['ball_no'][i] = ipl['ball_no'][i-1] + 1
print('ball number completed.')

ipl['balls'] = ipl['ball_no'] % 6
print('balls completed.')

for i in ipl.index:
    if ipl['balls'][i] == 0:
        ipl['overs'][i] += 1
print('overs completed.')

max_balls = pd.DataFrame(ipl.groupby(['match_id', 'innings'])['ball_no'].max())
max_balls.rename(columns = {'ball_no' : 'max_balls'}, inplace = True)
max_balls.reset_index(inplace = True)
ipl = ipl.merge(max_balls, on = ['match_id', 'innings'], how = 'left')
ipl['balls_remaining'] = 0
for i in ipl.index:
    if ipl['innings'][i] == 1:
        ipl['balls_remaining'][i] = ipl['max_balls'][i] - ipl['ball_no'][i]
    else:
        ipl['balls_remaining'][i] = (ipl['target_overs'][i] * 6) - ipl['ball_no'][i]
print('balls remaining completed.')

ipl['runs_scored_in_remaining_balls'] = 0
ipl['runs_required'] = 0
for i in ipl.index:
    if ipl['innings'][i] == 1:
        ipl['runs_scored_in_remaining_balls'][i] = ipl['final_score'][i] - ipl['runs'][i]
    else:
        ipl['runs_required'][i] = ipl['target_runs'][i] - ipl['runs'][i]
print('runs scored/required completed.')

won = []
for i in ipl.index:
    if ipl['batting_team'][i] == ipl['winner'][i]:
        won.append(1)
    else:
        won.append(0)
ipl['won'] = won
print('won column created.')

for col in ['team1', 'team2', 'batting_team', 'bowling_team']:
    t_list = []
    for i in ipl[col]:
        if i == 'Delhi Daredevils':
            t_list.append('Delhi Capitals')
        elif i == 'Rising Pune Supergiants':
            t_list.append('Rising Pune Supergiant')
        elif i == 'Kings XI Punjab':
            t_list.append('Punjab Kings')
        else:
            t_list.append(i)
    ipl[col] = t_list
print(col + ' cleaned.')

t_list = []
for i in ipl['venue']:
    if i == 'M.Chinnaswamy Stadium':
        t_list.append('M Chinnaswamy Stadium')
    elif i == 'MA Chidambaram Stadium, Chepauk, Chennai':
        t_list.append('MA Chidambaram Stadium')
    elif i == 'MA Chidambaram Stadium, Chepauk':
        t_list.append('MA Chidambaram Stadium')
    elif i == 'Subrata Roy Sahara Stadium':
        t_list.append('Maharashtra Cricket Association Stadium')
    elif i == 'Sardar Patel Stadium, Motera':
        t_list.append('Narendra Modi Stadium')
    elif i == 'Narendra Modi Stadium, Ahmedabad':
        t_list.append('Narendra Modi Stadium')
    elif i == 'Wankhede Stadium, Mumbai':
        t_list.append('Wankhede Stadium')
    elif i == 'Feroz Shah Kotla':
        t_list.append('Arun Jaitley Stadium')
    elif i == 'Arun Jaitley Stadium, Delhi':
        t_list.append('Arun Jaitley Stadium')
    elif i == 'Brabourne Stadium, Mumbai':
        t_list.append('Brabourne Stadium')
    elif i == 'Punjab Cricket Association IS Bindra Stadium, Mohali':
        t_list.append('Punjab Cricket Association IS Bindra Stadium')
    elif i == 'Punjab Cricket Association Stadium, Mohali':
        t_list.append('Punjab Cricket Association IS Bindra Stadium')
    elif i == 'Rajiv Gandhi International Stadium, Uppal':
        t_list.append('Rajiv Gandhi International Stadium')
    elif i == 'Zayed Cricket Stadium, Abu Dhabi':
        t_list.append('Sheikh Zayed Stadium')
    elif i == 'Vidarbha Cricket Association Stadium, Jamtha':
        t_list.append('Vidarbha Cricket Association Stadium')
    else:
        t_list.append(i)
ipl['venue'] = t_list
print('venue cleaned.')

ipl = ipl[['match_id', 'year', 'date', 'city', 'venue', 'team1', 'team2', 'toss_winner', 'toss_decision', 'innings', 'batting_team', 
           'bowling_team', 'batsman', 'non_striker', 'bowler', 'overs', 'balls', 'batsman_runs', 'extra_runs', 'total_runs', 
           'non_boundary', 'is_wicket', 'dismissal_kind', 'player_dismissed', 'fielder', 'extras_type', 'runs', 'wickets', 'runs_last_5_overs', 
           'wickets_last_5_overs', 'target_overs', 'target_runs', 'balls_remaining', 'runs_scored_in_remaining_balls', 'runs_required', 
           'winner', 'result', 'result_margin', 'player_of_match', 'playoff', 'knockout', 'final', 'method', 'players', 'umpire1', 'umpire2', 
           'final_score', 'total_wickets']]
ipl_1 = ipl[ipl['innings'] == 1]
ipl_2 = ipl[ipl['innings'] == 2]

matches = matches.merge(ipl_1[['match_id', 'final_score', 'total_wickets']], on = 'match_id', how = 'left')
matches.drop_duplicates(inplace = True)
matches.rename(columns = {'final_score' : 'innings_1_score', 'total_wickets' : 'innings_1_wickets'}, inplace = True)
matches = matches.merge(ipl_2[['match_id', 'final_score', 'total_wickets']], on = 'match_id', how = 'left')
matches.drop_duplicates(inplace = True)
matches.rename(columns = {'final_score' : 'innings_2_score', 'total_wickets' : 'innings_2_wickets'}, inplace = True)
print('Scores and wickets added to matches.')

innings_1_bat_team, innings_2_bat_team = [], []
for i in matches.index:
    if (matches['team1'][i] == matches['toss_winner'][i]) and (matches['toss_decision'][i] == 'bat'):
        innings_1_bat_team.append(matches['team1'][i])
        innings_2_bat_team.append(matches['team2'][i])
    elif (matches['team1'][i] == matches['toss_winner'][i]) and (matches['toss_decision'][i] == 'field'):
        innings_1_bat_team.append(matches['team2'][i])
        innings_2_bat_team.append(matches['team1'][i])
    elif (matches['team2'][i] == matches['toss_winner'][i]) and (matches['toss_decision'][i] == 'bat'):
        innings_1_bat_team.append(matches['team2'][i])
        innings_2_bat_team.append(matches['team1'][i])
    elif (matches['team2'][i] == matches['toss_winner'][i]) and (matches['toss_decision'][i] == 'field'):
        innings_1_bat_team.append(matches['team1'][i])
        innings_2_bat_team.append(matches['team2'][i])
    else:
        innings_1_bat_team.append(np.nan)
        innings_2_bat_team.append(np.nan)
matches['innings_1_bat_team'] = innings_1_bat_team
matches['innings_2_bat_team'] = innings_2_bat_team
print('Batting and bowling teams added to matches.')

matches.to_sql(name = 'match_list', con = engine, if_exists = 'append', chunksize = 1500, index = None)
ipl.to_sql(name = 'match_details', con = engine, if_exists = 'append', chunksize = 5000, index = None)
print('Data pushed to DB.')

for file in new:
    os.replace('Matches New\\' + file, 'Matches\\' + file)
print('Files moved to Matches folder.')