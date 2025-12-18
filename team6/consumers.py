import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from team6.game_logic.tictactoe import TicTacToe

# --- 1. マッチング用 (不具合修正版) ---
class MatchmakingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if not self.user.is_authenticated:
            await self.close()
            return
        await self.accept()

        # 現在の待機情報を取得
        waiting_data = await database_sync_to_async(cache.get)("waiting_player_data")

        # マッチング条件: 待機者がいて、かつ自分自身ではないこと
        if waiting_data and waiting_data['username'] != self.user.username:
            # マッチング成立！ 待機列を即座にクリア
            await database_sync_to_async(cache.delete)("waiting_player_data")
            
            new_room_name = f"match_{uuid.uuid4().hex[:8]}"
            
            # 自分に通知
            await self.send(text_data=json.dumps({
                'type': 'match_found', 'room_name': new_room_name
            }))
            # 相手(待機者)に通知
            await self.channel_layer.send(
                waiting_data['channel_name'],
                {'type': 'match_found_event', 'room_name': new_room_name}
            )
        else:
            # 待機列に自分を登録 (重複を防ぐため上書き)
            new_waiting_data = {
                'channel_name': self.channel_name,
                'username': self.user.username
            }
            await database_sync_to_async(cache.set)("waiting_player_data", new_waiting_data, 60)
            await self.send(text_data=json.dumps({'type': 'waiting'}))

    async def disconnect(self, close_code):
        # 自分が待機者だった場合、接続が切れたら待機列から削除（ゴースト防止）
        waiting_data = await database_sync_to_async(cache.get)("waiting_player_data")
        if waiting_data and waiting_data['channel_name'] == self.channel_name:
            await database_sync_to_async(cache.delete)("waiting_player_data")

    async def match_found_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'match_found', 'room_name': event['room_name']
        }))

# --- 2. ゲーム対戦用 (再入室対応版) ---
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

        room_key = f"game_state_{self.room_name}"
        room_data = await database_sync_to_async(cache.get)(room_key)

        if not room_data:
            # 最初の1人目
            room_data = {
                'board': [' ' for _ in range(9)],
                'current_player': 'X',
                'player_x': self.user.username,
                'player_o': None,
                'game_over': False,
                'winner': None,
                'winning_line': []
            }
        elif room_data['player_o'] is None and room_data['player_x'] != self.user.username:
            # 2人目
            room_data['player_o'] = self.user.username
            # 全員に開始演出を通知
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_start_event',
                    'player_x': room_data['player_x'],
                    'player_o': room_data['player_o']
                }
            )
        
        # 状態を保存してブロードキャスト
        await database_sync_to_async(cache.set)(room_key, room_data, 3600)
        await self.broadcast_state(room_data)

    async def receive(self, text_data):
        data = json.loads(text_data)
        room_key = f"game_state_{self.room_name}"
        room_data = await database_sync_to_async(cache.get)(room_key)

        if not room_data or room_data['game_over']:
            if data.get('type') == 'reset':
                await self.handle_reset()
            return

        if data.get('type') == 'move':
            # 手番バリデーション
            current_mark = room_data['current_player']
            allowed_user = room_data['player_x'] if current_mark == 'X' else room_data['player_o']
            
            if self.user.username != allowed_user:
                return

            game = TicTacToe()
            game.board = room_data['board']
            game.current_player = current_mark
            
            position = int(data.get('position', -1))
            if game.make_move(position)['success']:
                res = game.get_state()
                room_data.update({
                    'board': res['board'],
                    'current_player': res['current_player'],
                    'game_over': res['game_over'],
                    'winner': res['winner'],
                    'winning_line': res.get('winning_line', [])
                })
                await database_sync_to_async(cache.set)(room_key, room_data, 3600)
                await self.broadcast_state(room_data)

    async def handle_reset(self):
        room_key = f"game_state_{self.room_name}"
        room_data = await database_sync_to_async(cache.get)(room_key)
        if room_data:
            room_data.update({
                'board': [' ' for _ in range(9)],
                'current_player': 'X',
                'game_over': False,
                'winner': None,
                'winning_line': []
            })
            await database_sync_to_async(cache.set)(room_key, room_data, 3600)
            await self.broadcast_state(room_data)

    async def broadcast_state(self, room_data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'game_update_event', 'state': room_data}
        )

    async def game_update_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            **event['state']
        }))

    async def game_start_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'game_start',
            'player_x': event['player_x'],
            'player_o': event['player_o']
        }))