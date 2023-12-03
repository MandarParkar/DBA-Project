select count(*) from tournament;

select count(*) from team;

select count(*) from game;

select count(*) from score;

select * from game as g
inner join score as s
on g."game_id" = s."game_id"
inner join (select team."team_id", tournament."tournament", tournament."country" from team
				inner join tournament
				on team."tournament_id" = tournament."tournament_id") as t
on g."home_team_id" = t."team_id";

with cte as (select * from team
				inner join tournament
				on team."tournament_id" = tournament."tournament_id")
select * from game as g
inner join score as s
on g."game_id" = s."game_id"
inner join cte as cte1
on g."home_team_id" = cte1."team_id"
inner join cte as cte2
on g."away_team_id" = cte2."team_id";

with cte as (select * from team
				inner join tournament
				on team."tournament_id" = tournament."tournament_id")
select cte1."team" as home_team, cte2."team" as away_team, cte1."tournament" as tournament, 
cte1."country" as country, g."game_date" as game_date, s."game_minute" as game_minute, s."home_score" as home_score, 
s."away_score" as away_score
from game as g
inner join score as s
on g."game_id" = s."game_id"
inner join cte as cte1
on g."home_team_id" = cte1."team_id"
inner join cte as cte2
on g."away_team_id" = cte2."team_id" 
where cte2."tournament" = 'LaLiga';


select * from gamepoint."team"
				inner join gamepoint."tournament"
				on gamepoint."team"."tournament_id" = gamepoint."team"."tournament_id";





