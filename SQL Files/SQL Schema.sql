drop table if exists gamepoint.score;
drop table if exists gamepoint.game;
drop table if exists gamepoint.team;
drop table if exists gamepoint.tournament;

create table if not exists gamepoint.tournament(
	tournament_id int,
    tournament varchar(30),
    country varchar(30),
    constraint tournament_pk primary key (tournament_id)
);

create table if not exists gamepoint.team(
	team_id int,
    team varchar(50),
    tournament_id int,
    constraint team_pk primary key (team_id),
    constraint team_tournament_fk foreign key (tournament_id) references gamepoint.tournament(tournament_id) on delete cascade
);

create table if not exists gamepoint.game(
	game_id int,
    home_team_id int,
    away_team_id int,
    tournament_id int,
    game_date date,
    constraint game_pk primary key (game_id),
    constraint home_team_fk foreign key (home_team_id) references gamepoint.team(team_id) on delete cascade,
    constraint away_team_fk foreign key (away_team_id) references gamepoint.team(team_id) on delete cascade,
    constraint game_tournament_fk foreign key (tournament_id) references gamepoint.tournament(tournament_id) on delete cascade
);

create table if not exists gamepoint.score(
	score_id int,
    game_id int,
    game_minute smallint,
    home_score smallint,
    away_score smallint,
    constraint score_pk primary key (score_id),
    constraint game_fk foreign key (game_id) references gamepoint.game(game_id) on delete cascade
);
