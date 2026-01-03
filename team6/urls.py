from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # メニュー画面 (ここを入り口にする)
    path('', views.tictactoe_menu, name='tictactoe'),

    # オフライン対戦
    path('offline/', views.tictactoe_offline, name='tictactoe_offline'),

    # オンライン対戦 (ルーム指定)
    path('room/<path:room_name>/', views.tictactoe_game, name='tictactoe_room'),

    # その他
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Eカード
    path('ecard/', views.ecard_menu, name='ecard_menu'), # メニュー
    path('ecard/room/<path:room_name>/', views.ecard_game, name='ecard_room'),
]