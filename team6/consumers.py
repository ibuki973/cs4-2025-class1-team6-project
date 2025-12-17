import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from team6.game_logic.tictactoe import TicTacToe
# game_utils がない場合は try-except でエラー回避
try:
    from team6.game_logic.game_utils import get_winning_line
except ImportError:
    get_winning_line = None

# --- 1. マッチング用 ---
class MatchmakingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
        await self.accept()

        # 待機列を確認
        waiting_channel = await database_sync_to_async(cache.get)("waiting_player_channel")

        if waiting_channel:
            # マッチング成立！
            await database_sync_to_async(cache.delete)("waiting_player_channel")
            new_room_name = f"match_{uuid.uuid4().hex[:8]}"
            
            # 自分に通知
            await self.send(text_data=json.dumps({
                'type': 'match_found', 'room_name': new_room_name
            }))
            # 相手に通知
            await self.channel_layer.send(
                waiting_channel,
                {'type': 'match.found.event', 'room_name': new_room_name}
            )
        else:
            # 待機列に並ぶ
            await database_sync_to_async(cache.set)("waiting_player_channel", self.channel_name, 60)
            await self.send(text_data=json.dumps({'type': 'waiting'}))

    async def match_found_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'match_found', 'room_name': event['room_name']
        }))

# --- 2. ゲーム用 (レート機能付き) ---
class TicTacToeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'tictactoe_{self.room_name}'
        self.user = self.scope["user"]
        self.game = TicTacToe()

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # 初期状態送信
        await self.send(text_data=json.dumps(self._get_broadcast_data()))
        
        # 参加情報を通知
        if self.user.is_authenticated:
            rating = await self.get_rating(self.user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'player_joined_event', 'username': self.user.username, 'rating': rating}
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type') or data.get('action') # 両方に対応

        if msg_type == 'move':
            position = int(data.get('position', data.get('index', -1)))
            if self.game.make_move(position)['success']:
                state = self.game.get_state()
                # 勝敗がついた場合の処理
                if state['game_over'] and state['winner']:
                    await self.handle_game_over(state['winner'])
                
                # 全員に更新通知
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {'type': 'game_update_event', 'message': self._get_broadcast_data()}
                )
        
        elif msg_type == 'reset':
            self.game.reset()
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'game_update_event', 'message': self._get_broadcast_data()}
            )

    # --- ヘルパーメソッド ---
    async def handle_game_over(self, winner_mark):
        # 簡易実装: 勝った瞬間にサーバー側でレート更新を試みる
        # ※本来はプレイヤーの対応付けが必要ですが、今回は「この通信を送った人＝勝者」などの簡易判定もなしで、
        #   単純に勝敗ログを残すか、またはここで更新処理を呼び出します。
        pass 

    def _get_broadcast_data(self):
        state = self.game.get_state()
        winning_line = None
        if state['game_over'] and get_winning_line:
            try:
                winning_line = get_winning_line(state['board'])
            except: pass
        
        return {
            'type': 'game_state',
            'board': state['board'],
            'current_player': state['current_player'],
            'game_over': state['game_over'],
            'winner': state['winner'],
            'winning_line': winning_line
        }

    # --- イベントハンドラ ---
    async def game_update_event(self, event):
        await self.send(text_data=json.dumps(event['message']))
    
    async def player_joined_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_joined', 
            'username': event['username'], 
            'rating': event['rating']
        }))

    # --- DB操作 ---
    @database_sync_to_async
    def get_rating(self, user):
        from team6.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile.rating