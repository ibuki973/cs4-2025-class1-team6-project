from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # ログインページ (現在空のHTMLがありますが、一旦ルートに配置)
    path('', views.tictactoe_game, name='tictactoe'), 
    # ゲームルームごとのURLを許可する場合
    path('<str:room_name>/', views.tictactoe_game, name='tictactoe_room'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
]