from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

# Create your views here.

def tictactoe_game(request, room_name="lobby"):
    """
    三目並べゲームページをレンダリングする
    """
    context = {
        'room_name': room_name
    }
    # room_nameをコンテキストとして渡し、テンプレートをレンダリング
    return render(request, 'team6/Tic-Tac-Toe.html', context)

#ログインしていないとき自動で/login/に飛ばす

def dashboard(request):
    return render(request, 'team6/dashboard.html')