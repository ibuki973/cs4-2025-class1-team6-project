import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from team6.game_logic.tictactoe import TicTacToe

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
            # マッチング成立
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

# --- 2. ゲーム対戦用 (ターンバリデーション追加) ---
class TicTacToeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'tictactoe_{self.room_name}'
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # ルーム情報をキャッシュから取得 (ルーム内全員で状態を共有)
        room_key = f"game_state_{self.room_name}"
        room_data = await database_sync_to_async(cache.get)(room_key)

        if not room_data:
            # 最初の1人目を先行(X)として登録
            room_data = {
                'board': [' ' for _ in range(9)],
                'current_player': 'X',
                'player_x': self.user.username,
                'player_o': None,
                'game_over': False,
                'winner': None
            }
        elif room_data['player_o'] is None and room_data['player_x'] != self.user.username:
            # 2人目を後攻(O)として登録
            room_data['player_o'] = self.user.username

        await database_sync_to_async(cache.set)(room_key, room_data, 3600)
        
        # 参加情報をブロードキャスト
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_update_event',
                'state': room_data
            }
        )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')

        if msg_type == 'move':
            await self.handle_move(data)
        elif msg_type == 'reset':
            await self.handle_reset()

    async def handle_move(self, data):
        room_key = f"game_state_{self.room_name}"
        room_data = await database_sync_to_async(cache.get)(room_key)

        # 相手がいない場合や終了後は無視
        if not room_data or room_data['player_o'] is None or room_data['game_over']:
            return

        # --- 課題1: 自分のターンかどうかのバリデーション ---
        current_mark = room_data['current_player']
        allowed_user = room_data['player_x'] if current_mark == 'X' else room_data['player_o']

        # 送信者が現在の手番のユーザーでない場合は操作を拒否
        if self.user.username != allowed_user:
            return

        # ゲームロジックの実行
        game = TicTacToe()
        game.board = room_data['board']
        game.current_player = current_mark
        game.game_over = room_data['game_over']

        position = int(data.get('position', -1))
        result = game.make_move(position)

        if result['success']:
            new_state = game.get_state()
            room_data.update({
                'board': new_state['board'],
                'current_player': new_state['current_player'],
                'game_over': new_state['game_over'],
                'winner': new_state['winner']
            })
            await database_sync_to_async(cache.set)(room_key, room_data, 3600)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_update_event',
                    'state': room_data
                }
            )

    async def handle_reset(self):
        room_key = f"game_state_{self.room_name}"
        room_data = await database_sync_to_async(cache.get)(room_key)
        if room_data:
            room_data.update({
                'board': [' ' for _ in range(9)],
                'current_player': 'X',
                'game_over': False,
                'winner': None
            })
            await database_sync_to_async(cache.set)(room_key, room_data, 3600)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_update_event',
                    'state': room_data
                }
            )

    async def game_update_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            **event['state']
        }))