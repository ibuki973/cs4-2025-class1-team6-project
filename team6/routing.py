from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # 1. ランダムマッチング用
    re_path(r'ws/matchmaking/$', consumers.MatchmakingConsumer.as_asgi()),

    # 2. ゲーム対戦用 (tictactoe)
    re_path(r'ws/tictactoe/(?P<room_name>[^/]+)/$', consumers.TicTacToeConsumer.as_asgi()),
    
    re_path(r'ws/game/(?P<room_name>[^/]+)/$', consumers.TicTacToeConsumer.as_asgi()),
    re_path(r'ws/hitandblow/(?P<room_name>[^/]+)/$', consumers.HitAndBlowConsumer.as_asgi()),
=======
    
    # Eカード用
    re_path(r'ws/ecard/(?P<room_name>[^/]+)/$', consumers.ECardConsumer.as_asgi()),
]