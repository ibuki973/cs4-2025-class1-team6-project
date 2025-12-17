from django.db import models
from django.conf import settings

class GameRecord(models.Model):
    """
    対戦履歴を保存するモデル
    """
    # プレイヤー1 (必須)
    player1 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='games_as_p1', on_delete=models.CASCADE)
    
    # プレイヤー2 (CPU対戦や一人用モードも考慮してnull許容にしておくが、オンライン対戦では必須)
    player2 = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='games_as_p2', on_delete=models.CASCADE, null=True, blank=True)
    
    # 勝者 (引き分けの場合は null)
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='games_won', on_delete=models.SET_NULL, null=True, blank=True)
    
    # 対戦日時 (自動的に現在の時刻が入る)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Match: {self.player1} vs {self.player2} - Winner: {self.winner}"