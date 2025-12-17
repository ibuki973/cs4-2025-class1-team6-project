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

# --- 2. ゲーム対戦用 ---
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
            # 初期状態に winning_line を追加
            room_data = {
                'board': [' ' for _ in range(9)],
                'current_player': 'X',
                'player_x': self.user.username,
                'player_o': None,
                'game_over': False,
                'winner': None,
                'winning_line': [] # 追加
            }
        elif room_data['player_o'] is None and room_data['player_x'] != self.user.username:
            room_data['player_o'] = self.user.username
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_start_event',
                    'player_x': room_data['player_x'],
                    'player_o': room_data['player_o']
                }
            )

        await database_sync_to_async(cache.set)(room_key, room_data, 3600)
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'game_update_event', 'state': room_data}
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

        if not room_data or room_data['player_o'] is None or room_data['game_over']:
            return

        current_mark = room_data['current_player']
        allowed_user = room_data['player_x'] if current_mark == 'X' else room_data['player_o']

        if self.user.username != allowed_user:
            return

        game = TicTacToe()
        game.board = room_data['board']
        game.current_player = current_mark
        game.game_over = room_data['game_over']
        # winning_lineは再構築時は不要だが、状態管理のために一応取得
        game.winning_line = room_data.get('winning_line', [])

        position = int(data.get('position', -1))
        result = game.make_move(position)

        if result['success']:
            new_state = game.get_state()
            room_data.update({
                'board': new_state['board'],
                'current_player': new_state['current_player'],
                'game_over': new_state['game_over'],
                'winner': new_state['winner'],
                'winning_line': new_state['winning_line'] # 更新
            })
            await database_sync_to_async(cache.set)(room_key, room_data, 3600)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'game_update_event', 'state': room_data}
            )

    async def handle_reset(self):
        room_key = f"game_state_{self.room_name}"
        room_data = await database_sync_to_async(cache.get)(room_key)
        if room_data:
            # リセット時に winning_line もクリア
            room_data.update({
                'board': [' ' for _ in range(9)],
                'current_player': 'X',
                'game_over': False,
                'winner': None,
                'winning_line': [] # クリア
            })
            await database_sync_to_async(cache.set)(room_key, room_data, 3600)
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