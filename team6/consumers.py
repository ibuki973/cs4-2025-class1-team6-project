from channels.generic.websocket import AsyncWebsocketConsumer
from team6.game_logic import TicTacToe  # ← インポート
import json

class TicTacToeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'tictactoe_{self.room_name}'
        
        # ゲームインスタンスを作成
        self.game = TicTacToe()  # ← ここで使用
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    
    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            position = int(data.get('position'))
            
            # ゲームロジック実行 ← ここで使用
            result = self.game.make_move(position)
            
            # すべてのクライアントに状態を送信
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_update',
                    'message': result
                }
            )
        except Exception as e:
            await self.send(text_data=json.dumps({
                'error': str(e)
            }))
    
    async def game_update(self, event):
        await self.send(text_data=json.dumps(event['message']))