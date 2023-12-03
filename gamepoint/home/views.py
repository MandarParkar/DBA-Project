from django.shortcuts import render, HttpResponse
from .models import Game, Tournament, Team, Score
from django.db import connection
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from datetime import datetime
import time

from django.conf import settings

cassandra_settings = { 'HOST': '3.228.202.168', 'PORT' : '9042' , "KEYSPACE" : 'gamepoint', 'USERNAME' : 'cassandra', 'PASSWORD' : 'cassandra'}


def home(request):

    return render(request, 'index.html')

def livematchs(request):
    allTeams = getAllMatch()
    allTournaments = getAllTournaments()
    allRows, count, execution_time = getRandomMatches()
    sucess_message = {'count': count, 'execution_time':round(execution_time, 4)}

    if request.method != 'POST':
        return render(request, 'livematchs.html', {'matchs' : allRows, 'teams': allTeams, 'allTournaments': allTournaments, 'error_message': None, 'sucess_message': sucess_message})

    elif request.method == 'POST':
        teamName = request.POST.get('dropdown1')
        tournamentName = request.POST.get('dropdown2')
        startdate = request.POST.get('startDate')
        endDate = request.POST.get('endDate')
        scoreShow = request.POST.get('getScore')

        teamName = teamName.lower()
        tournamentName = tournamentName.lower()

        error_message, isError = handleFilterError(teamName, tournamentName, startdate, endDate, scoreShow)
        if isError:
            return render(request, 'livematchs.html', {'matchs' : allRows, 'teams': allTeams, 'allTournaments': allTournaments, 'error_message': error_message, 'sucess_message': sucess_message})

        games_list = []

        if scoreShow=='showRow':
            games_list, count, execution_time = getGameAndDetails(startdate, endDate, tournamentName, teamName)
            sucess_message = {'count': count, 'execution_time':round(execution_time, 4)}
        elif scoreShow=='hideRow':
            games_list, count, execution_time = getGameWithoutDetails(startdate, endDate,tournamentName, teamName)
            sucess_message = {'count': count, 'execution_time':round(execution_time, 4)}


        return render(request, 'livematchs.html', {'matchs' : games_list,'teams': allTeams, 'allTournaments': allTournaments, 'error_message': error_message, 'sucess_message': sucess_message})

    # else:
    #     return render(request, 'livematchs.html', {'matchs' : allRows, 'teams': allTeams, 'allTournaments': allTournaments, 'error_message': None})

def oldmatchs(request):
    # allrows = cassandraQuery()
    allTeams = getCassandraAllteams()
    allTournaments = getCassandraAlltournament()
    allRows,count, execution_time = getCassandraRandomMatches()
    sucess_message = {'count': count, 'execution_time':round(execution_time, 4)}
    

    if request.method != 'POST':
        return render(request, 'oldmatchs.html', {'matchs' : allRows, 'teams': allTeams, 'allTournaments': allTournaments, 'error_message': None,  'sucess_message': sucess_message})

    elif request.method == 'POST':
        teamName = request.POST.get('dropdown1')
        tournamentName = request.POST.get('dropdown2')
        startdate = request.POST.get('startDate')
        endDate = request.POST.get('endDate')
        scoreShow = request.POST.get('getScore')

        # teamName = teamName.lower()
        # tournamentName = tournamentName.lower()

        error_message, isError = handleFilterError(teamName, tournamentName, startdate, endDate, scoreShow)
        if isError:
            return render(request, 'oldmatchs.html', {'matchs' : allRows, 'teams': allTeams, 'allTournaments': allTournaments, 'error_message': error_message,  'sucess_message': sucess_message})

        games_list = []

        if scoreShow=='showRow':
            games_list, count, execution_time = getGameWithDetailsCassandra(startdate, endDate,tournamentName, teamName)
            sucess_message = {'count': count, 'execution_time':round(execution_time, 4)}
        elif scoreShow=='hideRow':
            games_list, count, execution_time = getGameWithoutDetailsCassandra(startdate, endDate,tournamentName, teamName)
            sucess_message = {'count': count, 'execution_time':round(execution_time, 4)}


    return render(request, 'oldmatchs.html', {'matchs' : games_list,'teams': allTeams, 'allTournaments': allTournaments, 'error_message': error_message,  'sucess_message': sucess_message})

def getAllMatch():
    allTeams = """
    select distinct team from gamepoint."team";
    """

    with connection.cursor() as cursorTeams:
        cursorTeams.execute(allTeams)
        teams = cursorTeams.fetchall()

    allTeams = []
    for i in range(len(teams)):
        
        teams[i] = teams[i][0]
        d = {'team' : teams[i]}
        allTeams.append(d)

    return allTeams

def getAllTournaments():
    allTournament = """
    select distinct tournament from gamepoint."tournament";
    """
    with connection.cursor() as cursorTournament:
        cursorTournament.execute(allTournament)
        Tournaments = cursorTournament.fetchall()

    allTournaments = []
    for i in range(len(Tournaments)):
        
        Tournaments[i] = Tournaments[i][0]
        d = {'Tournaments' : Tournaments[i]}
        allTournaments.append(d)

    return allTournaments

# def cassandraQuery():
#     rows = session.execute("SELECT * FROM gamepoint")
#     allRows = []
#     for row in rows:
#         date_string = f"{row.year}-{row.month:02d}-{row.day:02d}"  # Format: YYYY-MM-DD
#         date_object = datetime.strptime(date_string, "%Y-%m-%d")
#         formatted_date = date_object.strftime("%B %d, %Y")
#         game = {
#         'homeTeam': row.home_team,
#         'awayTeam': row.away_team,
#         'tournament': row.tournament,
#         'country': row.country,
#         'gameDate': formatted_date,
#         'gameMinute': row.minute,
#         'FinalScore': {'HomeFinal': row.home_score, 'AwayFinal': row.away_score}
#     }
#         allRows.append(game)
#     return allRows


def getRandomMatches():
    query = """
    with tournament_team as (select "team"."team_id", "team"."team", "team"."tournament_id", "tournament"."tournament", "tournament"."country" 
                from gamepoint."team" as "team"
                inner join gamepoint."tournament" as "tournament"
                on "team"."tournament_id" = "tournament"."tournament_id")
    select "game"."game_id", "cte1"."team_id" as home_team_id, "cte2"."team_id" as away_team_id, 
    cte1."team" as home_team, cte2."team" as away_team, cte1."tournament" as tournament, 
    cte1."country" as country, "game"."game_date" as game_date, "score"."game_minute" as game_minute, 
    "score"."home_score" as home_score, "score"."away_score" as away_score
        from gamepoint."game" as game
        inner join gamepoint."score" as score
        on "game"."game_id" = "score"."game_id"
        inner join tournament_team as cte1
        on cte1."team_id" = "game"."home_team_id"
        inner join tournament_team as cte2
        on cte2."team_id" = "game"."away_team_id"
        where "score"."game_minute" = 90
        order by "game"."game_date" desc, "score"."game_minute"
        Limit 10;
    """
   
    start_time = time.time()
    with connection.cursor() as cursor:
        
        cursor.execute(query)
        rows = cursor.fetchall()
    end_time = time.time()
    
    execution_time = end_time - start_time
        
    allRows = []
    for row in rows:
        dict = {
            'homeTeam' : row[3],
            'awayTeam' : row[4],
            'tournament' : row[5],
            'country' : row[6],
            'gameDate' : row[7],
            'gameMinute' : row[8],
            'FinalScore': {'HomeFinal' : row[9], 'AwayFinal' : row[10]}
        }
        allRows.append(dict)
    count = len(allRows)
    return allRows, count, execution_time

def getCassandraAllteams():
    teams = session.execute("SELECT * FROM team;")
    allTeams = []
    for team in teams:
        d = {'team' : team.team}
        allTeams.append(d)
    return allTeams

def getCassandraAlltournament():
    tournaments = session.execute("SELECT * FROM tournament;")
    allTournament = []
    for tournament in tournaments:
        d = {'Tournaments' : tournament.tournament}
        allTournament.append(d)
    return allTournament

def getCassandraRandomMatches():
    start_time = time.time()
    randomMatchs = session.execute("SELECT * FROM gamepoint WHERE game_minute = 90 Limit 10 ALLOW FILTERING;")
    end_time = time.time()
    execution_time = end_time - start_time
    allRows = []
    for randomMatch in randomMatchs:
        # date_string = f"{int(randomMatch.year)}-{int(randomMatch.month):02d}-{int(randomMatch.day):02d}"  # Format: YYYY-MM-DD
        date_object = randomMatch.game_date
        formatted_date = date_object.strftime("%B %d, %Y")
        dict = {
            'homeTeam' : randomMatch.home_team,
            'awayTeam' : randomMatch.away_team,
            'tournament' : randomMatch.tournament,
            'country' : randomMatch.country,
            'gameDate' : formatted_date,
            'gameMinute' : randomMatch.game_minute,
            'FinalScore': {'HomeFinal' : randomMatch.home_score, 'AwayFinal' : randomMatch.away_score}
        }
        allRows.append(dict)
    count = len(allRows)
    return allRows, count, execution_time

def getGameWithoutDetailsCassandra(startdate, endDate, tournamentName, teamName):
    paramsFilter1 = (str(tournamentName), str(teamName), str(startdate), str(endDate))
    start_time = time.time()
    filterMatchNoShow1 = session.execute("SELECT * FROM gamepoint WHERE tournament = %s AND away_team = %s AND game_minute = 90 AND game_date >= %s AND game_date <= %s ALLOW FILTERING;", paramsFilter1)
    filterMatchNoShow2 = session.execute("SELECT * FROM gamepoint WHERE tournament = %s AND home_team = %s AND game_minute = 90 AND game_date >= %s AND game_date <= %s ALLOW FILTERING;", paramsFilter1)
    end_time = time.time()
    execution_time = end_time - start_time
    gamesAll = getAllRowsWithoutDetailsCassandra([], filterMatchNoShow1)
    gamesAll = getAllRowsWithoutDetailsCassandra(gamesAll, filterMatchNoShow2)
    
    return gamesAll, len(gamesAll), execution_time


def getAllRowsWithoutDetailsCassandra(gamesAll, matches):
    
    for match in matches:
        # date_string = f"{match.year}-{match.month:02d}-{match.day:02d}" 
        date_string = str(match.game_date)[:-9]
        date_object = datetime.strptime(date_string, "%Y-%m-%d")
        formatted_date = date_object.strftime("%B %d, %Y")
        dict = {
            'homeTeam' : match.home_team,
            'awayTeam' : match.away_team,
            'tournament' : match.tournament,
            'country' : match.country,
            'gameDate' : formatted_date,
            'gameMinute' : match.game_minute,
            'FinalScore': {'HomeFinal' : match.home_score, 'AwayFinal' : match.away_score}
        }
        gamesAll.append(dict)
    return gamesAll

def getGameWithDetailsCassandra(startdate, endDate, tournamentName, teamName):
    paramsFilter1 = (tournamentName, teamName, startdate, endDate)
    start_time = time.time()
    filterMatchNoShow1 = session.execute("SELECT * FROM gamepoint WHERE tournament = %s AND away_team = %s AND game_date >= %s AND game_date <= %s ALLOW FILTERING;", paramsFilter1)
    filterMatchNoShow2 = session.execute("SELECT * FROM gamepoint WHERE tournament = %s AND home_team = %s AND game_date >= %s AND game_date <= %s ALLOW FILTERING;", paramsFilter1)
    end_time = time.time()
    execution_time = end_time - start_time
    gamesAll = getAllRowsWithDetailsCassandra([], filterMatchNoShow1)
    gamesAll = getAllRowsWithDetailsCassandra(gamesAll, filterMatchNoShow2)
    # print('gamesAll', gamesAll)
    return gamesAll, len(gamesAll), execution_time

def getAllRowsWithDetailsCassandra(gamesAll, matches):
    games = {}

    for match in matches:
        # date_string = f"{match.year}-{match.month:02d}-{match.day:02d}"  # Format: YYYY-MM-DD
        date_string = str(match.game_date)[:-9]
        date_object = datetime.strptime(date_string, "%Y-%m-%d")
        formatted_date = date_object.strftime("%B %d, %Y")

        game_id = match.game_id
        if game_id not in games:
            games[game_id] = {
                'homeTeam' : match.home_team,
                'awayTeam' : match.away_team,
                'tournament' : match.tournament,
                'country' : match.country,
                'gameDate' : formatted_date,
                'gameMinute' : match.game_minute,
                'GameDetails': [],
                'FinalScore': {}
            }
        games[game_id]['GameDetails'].append({
            'gameMinute': match.game_minute,
            'homeScore':  match.home_score,
            'awayScore': match.away_score
        })

        if match.game_minute == 90:
            games[game_id]['FinalScore'] = {'HomeFinal' : match.home_score, 'AwayFinal' : match.away_score}

    gamesAll += games.values()
    return gamesAll


def getGameAndDetails(startdate, endDate,tournamentName, teamName):
    outputOfallRowsWithDetails, execution_time = queryForAllGamesWithRows(startdate, endDate,tournamentName, teamName)
    
    games = {}

    for row in outputOfallRowsWithDetails:
        game_id = row[0]
        if game_id not in games:
            games[game_id] = {
                'homeTeam': row[3],
                'awayTeam': row[4],
                'tournament': row[5],
                'country': row[6],
                'gameDate': row[7],
                'GameDetails': [],
                'FinalScore': {}
            }
        games[game_id]['GameDetails'].append({
            'gameMinute': row[8],
            'homeScore': row[9],
            'awayScore': row[10]
        })

        if row[8] == 90:
            games[game_id]['FinalScore'] = {'HomeFinal' : row[9], 'AwayFinal' : row[10]}

    games_list = list(games.values())
    count = len(games_list)
    return games_list, count, execution_time



def queryForAllGamesWithRows(startdate, endDate,tournamentName, teamName):
    queryFilter = """
        with tournament_team as (select "team"."team_id", "team"."team", "team"."tournament_id", "tournament"."tournament", 
                            "tournament"."country"
                                from gamepoint."team" as "team"
                                inner join gamepoint."tournament" as "tournament"
                                on "team"."tournament_id" = "tournament"."tournament_id")
    select "game"."game_id", "cte1"."team_id" as home_team_id, "cte2"."team_id" as away_team_id, 
    cte1."team" as home_team, cte2."team" as away_team, cte1."tournament" as tournament, 
    cte1."country" as country, "game"."game_date" as game_date, "score"."game_minute" as game_minute, 
    "score"."home_score" as home_score, "score"."away_score" as away_score
        from gamepoint."game" as game
        inner join gamepoint."score" as score
        on "game"."game_id" = "score"."game_id"
        inner join tournament_team as cte1
        on cte1."team_id" = "game"."home_team_id"
        inner join tournament_team as cte2
        on cte2."team_id" = "game"."away_team_id"
        where lower("cte1"."tournament") in (%s)
            and "game"."game_date" between %s and %s
            and (lower("cte1"."team") in (%s) or lower("cte2"."team") in (%s))
        order by "game"."game_date" desc, "score"."game_minute";
        """
    
    paramsFilter = (tournamentName,startdate, endDate, teamName, teamName)

    start_time = time.time()
    with connection.cursor() as cursorFilter:
        cursorFilter.execute(queryFilter, paramsFilter)
        executed_query = cursorFilter.mogrify(queryFilter, paramsFilter).decode('utf-8')
        # print("Executed Query:", executed_query)
        filter = cursorFilter.fetchall()

        
    end_time = time.time()
    execution_time = end_time - start_time

    return filter, execution_time

def getGameWithoutDetails(startdate, endDate, tournamentName, teamName):
    outputOfGameWithoutDetails, execution_time = QueryGameWithoutDetails(startdate, endDate, tournamentName, teamName)
    
    
    gamesAll = []
    for row in outputOfGameWithoutDetails:
        games = {
            'homeTeam': row[3],
            'awayTeam': row[4],
            'tournament': row[5],
            'country': row[6],
            'gameDate': row[7],
            'GameDetails': None,
            'FinalScore': {'HomeFinal' : row[9], 'AwayFinal' : row[10]}
        }
        gamesAll.append(games)
    count = len(gamesAll)
    return gamesAll, count, execution_time

def QueryGameWithoutDetails(startdate, endDate,tournamentName, teamName):
    queryFilter = """
        with tournament_team as (select "team"."team_id", "team"."team", "team"."tournament_id", "tournament"."tournament", 
                            "tournament"."country"
                                from gamepoint."team" as "team"
                                inner join gamepoint."tournament" as "tournament"
                                on "team"."tournament_id" = "tournament"."tournament_id")
    select "game"."game_id", "cte1"."team_id" as home_team_id, "cte2"."team_id" as away_team_id, 
    cte1."team" as home_team, cte2."team" as away_team, cte1."tournament" as tournament, 
    cte1."country" as country, "game"."game_date" as game_date, "score"."game_minute" as game_minute, 
    "score"."home_score" as home_score, "score"."away_score" as away_score
        from gamepoint."game" as game
        inner join gamepoint."score" as score
        on "game"."game_id" = "score"."game_id"
        inner join tournament_team as cte1
        on cte1."team_id" = "game"."home_team_id"
        inner join tournament_team as cte2
        on cte2."team_id" = "game"."away_team_id"
        where lower("cte1"."tournament") in (%s)
            and "game"."game_date" between %s and %s
            and (lower("cte1"."team") in (%s) or lower("cte2"."team") in (%s))
            and "score"."game_minute" = 90
        order by "game"."game_date" desc, "score"."game_minute"
        Limit 1000;
        """
    
    paramsFilter = (tournamentName, startdate, endDate, teamName, teamName)

    start_time = time.time()
    with connection.cursor() as cursorFilter:
        cursorFilter.execute(queryFilter, paramsFilter)
        executed_query = cursorFilter.mogrify(queryFilter, paramsFilter).decode('utf-8')
        # print("Executed Query:", executed_query)
        filter = cursorFilter.fetchall()
    
    end_time = time.time()
    execution_time = end_time - start_time

    return filter, execution_time



def handleFilterError(teamName, tournamentName, startdate, endDate, scoreShow):
    error_message = None
    if teamName==None:
        error_message = "Select Team."
    elif tournamentName==None:
        error_message = 'Select Tournament.'
    elif len(startdate)==0:
        error_message = "Enter start date in format MM/DD/YYYY."
    elif len(endDate)==0:
        error_message = "Enter end date in format MM/DD/YYYY."
    elif scoreShow==None:
        error_message = "Select if you want to see score details."
    if error_message!=None:
        return error_message, True
    return None, False



def get_cassandra_session():
    cluster = Cluster(
        [cassandra_settings['HOST']],
        port=cassandra_settings['PORT']
    )
    if 'USERNAME' in cassandra_settings and 'PASSWORD' in cassandra_settings:
        auth_provider = PlainTextAuthProvider(
            username=cassandra_settings['USERNAME'],
            password=cassandra_settings['PASSWORD']
        )
        cluster = Cluster(
            [cassandra_settings['HOST']],
            port=cassandra_settings['PORT'],
            auth_provider=auth_provider
        )
    session = cluster.connect(cassandra_settings['KEYSPACE'])
    return session



session = get_cassandra_session()