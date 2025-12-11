from django.urls import path
from . import views

urlpatterns = [
    # ログインページ (現在空のHTMLがありますが、一旦ルートに配置)
    path('', views.tictactoe_game, name='tictactoe'), 
    # ゲームルームごとのURLを許可する場合
    path('<str:room_name>/', views.tictactoe_game, name='tictactoe_room'),
]