from django.shortcuts import render
from django.http import HttpResponse

<<<<<<< HEAD
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
=======
def home(request):
    return HttpResponse("TEAM6: 動作確認OK")
>>>>>>> 3b251b33935677b1357414ccb7515d3bdbd3a351
