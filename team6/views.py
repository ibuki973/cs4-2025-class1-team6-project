from django.shortcuts import render
from django.contrib.auth.decorators import login_required

def tictactoe_menu(request):
    """メニュー画面（ルール説明とモード選択）"""
    return render(request, 'team6/tictactoe_menu.html')

def tictactoe_offline(request):
    """オフライン対戦モード"""
    return render(request, 'team6/tictactoe_offline.html')

def tictactoe_game(request, room_name="lobby"):
    """オンライン対戦モード"""
    context = {'room_name': room_name}
    return render(request, 'team6/Tic-Tac-Toe.html', context)

def dashboard(request):
    return render(request, 'team6/dashboard.html')