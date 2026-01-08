from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # --- 既存の三目並べ ---
    path('', views.tictactoe_menu, name='tictactoe'),
    path('offline/', views.tictactoe_offline, name='tictactoe_offline'),
    path('room/<path:room_name>/', views.tictactoe_game, name='tictactoe_room'),
    
    # --- Eカード用 (パスを少し短く調整) ---
    path('ecard/menu/', views.ecard_menu, name='ecard_menu'),
    path('ecard/room/<path:room_name>/', views.ecard_game, name='ecard_room'),
    
    # --- 共通 ---
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
]