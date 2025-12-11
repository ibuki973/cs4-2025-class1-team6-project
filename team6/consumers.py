from channels.generic.websocket import AsyncWebsocketConsumer
from team6.game_logic import TicTacToe
import json
# get_winning_line が game_utils にあるか確認、なければこの行は削除しても動きますが、
# 勝敗判定のハイライトに必要です。
from team6.game_logic.game_utils import get_winning_line 

class TicTacToeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'tictactoe_{self.room_name}'
        
        # ゲームインスタンスを作成
        self.game = TicTacToe()
        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
        
        print(f"★ [Connect] Client connected to room: {self.room_name}")

        # 【重要】初期状態を送信
        # データ構造を統一するため、_get_broadcast_data を使いつつ type を上書きします
        initial_data = self._get_broadcast_data()
        initial_data['type'] = 'initial_state'
        
        await self.send(text_data=json.dumps(initial_data))

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            print(f"★ [Receive] Type: {message_type}, Data: {data}")

            if message_type == 'move':
                # 1. 移動の処理
                position = int(data.get('position'))
                result = self.game.make_move(position)
                print(f"   -> Move result: {result['success']}, New Player: {self.game.current_player}")

            elif message_type == 'reset':
                # 2. リセットの処理
                self.game.reset()
                print("   -> Game reset")
            
            # 3. すべてのクライアントに状態をブロードキャスト
            # ここで _get_broadcast_data() が正しい辞書（type付き）を返すことが重要です
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_update',
                    'message': self._get_broadcast_data()
                }
            )
            
        except Exception as e:
            print(f"★ [Error] {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))
    
    async def game_update(self, event):
        # グループから受け取ったメッセージをそのままクライアントへ転送
        await self.send(text_data=json.dumps(event['message']))

    def _get_broadcast_data(self):
        """
        クライアントに送信するデータ構造を生成
        JavaScriptの updateGameDisplay が期待する形に整形します。
        """
        game_state = self.game.get_state()
        
        # 勝ちラインの取得（エラー回避のためtry-except）
        try:
            winning_line = get_winning_line(game_state['board'])
        except:
            winning_line = None

        # 【最重要】ここで必ず 'type': 'game_state' を含めること！
        return {
            'type': 'game_state', 
            'board': game_state['board'],
            'current_player': game_state['current_player'],
            'game_over': game_state['game_over'],
            'winner': game_state['winner'],
            'message': game_state.get('message', ''),
            'winning_line': winning_line
        }