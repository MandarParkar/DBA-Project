from django.db import models


# Create your models here.
class Tournament(models.Model):
    tournament_id = models.AutoField(primary_key=True)
    tournament = models.CharField(max_length=30)
    country = models.CharField(max_length=30)

    class Meta:
        db_table = 'tournament'
        managed = False

class Team(models.Model):
    team_id = models.AutoField(primary_key=True)
    team = models.CharField(max_length=50)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)

    class Meta:
        db_table = 'team'
        managed = False


class Game(models.Model):
    game_id = models.AutoField(primary_key=True)
    home_team = models.ForeignKey(Team, related_name='home_games', on_delete=models.CASCADE)
    away_team = models.ForeignKey(Team, related_name='away_games', on_delete=models.CASCADE)
    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE)
    game_date = models.DateField()

    class Meta:
        db_table = 'game'
        managed = False


class Score(models.Model):
    score_id = models.AutoField(primary_key=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    home_score = models.SmallIntegerField()
    away_score = models.SmallIntegerField()
    game_minute = models.SmallIntegerField()

    class Meta:
        db_table = 'score'
        managed = False

