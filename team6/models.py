from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- 既存のGameRecordはそのまま ---
class GameRecord(models.Model):
    player1 = models.ForeignKey(User, related_name='games_as_p1', on_delete=models.CASCADE)
    player2 = models.ForeignKey(User, related_name='games_as_p2', on_delete=models.CASCADE, null=True, blank=True)
    winner = models.ForeignKey(User, related_name='games_won', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Match: {self.player1} vs {self.player2} ({self.created_at})"

# ユーザープロフィール (レート管理)
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    rating = models.IntegerField(default=1500)  # 初期レート 1500

    def __str__(self):
        return f"{self.user.username} (Rate: {self.rating})"

# ユーザー作成時に自動的にプロフィールも作る設定
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()