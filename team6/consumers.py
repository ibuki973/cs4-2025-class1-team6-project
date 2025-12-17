import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache  # ★追加
from team6.game_logic.tictactoe import TicTacToe

# game_utils のインポート（エラー回避付き）
try:
    from team6.game_logic.game_utils import get_winning_line
except ImportError:
    get_winning_line = None

# --- 1. マッチング用 (ここは変更なし) ---
class MatchmakingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
        await self.accept()

        waiting_channel = await database_sync_to_async(cache.get)("waiting_player_channel")

        if waiting_channel:
            await database_sync_to_async(cache.delete)("waiting_player_channel")
            new_room_name = f"match_{uuid.uuid4().hex[:8]}"
            
            await self.send(text_data=json.dumps({
                'type': 'match_found', 'room_name': new_room_name
            }))
            await self.channel_layer.send(
                waiting_channel,
                {'type': 'match.found.event', 'room_name': new_room_name}
            )
        else:
            await database_sync_to_async(cache.set)("waiting_player_channel", self.channel_name, 60)
            await self.send(text_data=json.dumps({'type': 'waiting'}))

    async def match_found_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'match_found', 'room_name': event['room_name']
        }))

# --- 2. ゲーム用 (同期ロジック修正版) ---
class TicTacToeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'tictactoe_{self.room_name}'
        self.user = self.scope["user"]
        
        # ★重要: キャッシュキー (ルームごとに1つのキー)
        self.game_cache_key = f"game_state_{self.room_name}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # ゲーム状態のロードまたは初期化
        self.game = await self._load_or_create_game()

        # 最新状態を送信
        await self.send(text_data=json.dumps(self._get_broadcast_data()))
        
        # 参加通知
        if self.user.is_authenticated:
            rating = await self.get_rating(self.user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'player_joined_event', 'username': self.user.username, 'rating': rating}
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # team6/consumers.py の TicTacToeConsumer クラス内を修正

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type') or data.get('action')

        self.game = await self._load_or_create_game()
        state = self.game.get_state()

        if msg_type == 'move':
            # ★【追加】自分のターンかどうかのチェック
            # state['current_player'] ('X'か'O') と、自分の割り当てを比較
            # 簡易的に、最初に入った人をX、次をOとして判定するロジックが必要です。
            # 今回はJS側と連携し、許可されたマーク以外は無視するようにします。
            
            position = int(data.get('position', -1))
            
            # 誰のターンか判定するための情報を取得（JSから送られてきたマーク）
            player_mark = data.get('player_mark') 
            
            if state['current_player'] == player_mark:
                result = self.game.make_move(position)
                if result['success']:
                    await self._save_game()
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {'type': 'game_update_event', 'message': self._get_broadcast_data()}
                    )
        elif msg_type == 'reset':
            self.game.reset()
            await self._save_game() # リセット状態も保存
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'game_update_event', 'message': self._get_broadcast_data()}
            )

    # --- キャッシュ管理メソッド (ここが今回のキモ) ---
    @database_sync_to_async
    def _load_or_create_game(self):
        # キャッシュからデータを取得
        game_data = cache.get(self.game_cache_key)
        game = TicTacToe()
        
        if game_data:
            # データがあれば復元
            game.board = game_data['board']
            game.current_player = game_data['current_player']
            game.game_over = game_data['game_over']
            game.winner = game_data['winner']
        else:
            # なければ新規作成して保存
            cache.set(self.game_cache_key, game.get_state(), timeout=3600) # 1時間有効
            
        return game

    @database_sync_to_async
    def _save_game(self):
        # 現在の状態をキャッシュに保存
        cache.set(self.game_cache_key, self.game.get_state(), timeout=3600)

    # --- ヘルパーメソッド ---
    async def handle_game_over(self, winner_mark):
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