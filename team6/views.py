from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

# --- 既存のビュー ---

def tictactoe_menu(request):
    """メニュー画面"""
    return render(request, 'team6/tictactoe_menu.html')

def tictactoe_offline(request):
    """オフライン対戦モード"""
    return render(request, 'team6/tictactoe_offline.html')

def tictactoe_game(request, room_name="lobby"):
    """オンライン対戦モード"""
    context = {'room_name': room_name}
    return render(request, 'team6/Tic-Tac-Toe.html', context)

@login_required
def dashboard(request):
    """ダッシュボード"""
    return render(request, 'team6/dashboard.html')



def signup(request):
    """ユーザー新規登録"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 登録と同時にログインさせる
            login(request, user)
            # ダッシュボードへリダイレクト
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'team6/signup.html', {'form': form})
def hitandblow_game(request, room_name="lobby"):
    return render(request, 'team6/hitandblow.html', {'room_name': room_name})