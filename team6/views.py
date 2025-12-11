from django.shortcuts import render

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
