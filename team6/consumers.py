import json
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.contrib.auth.models import User
from team6.game_logic.tictactoe import TicTacToe
from team6.game_logic.game_utils import get_winning_line

# ==========================================
# 1. マッチング用コンシューマ (待機列管理)
# ==========================================
class MatchmakingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # ログインしていなければ切断
        if not self.scope["user"].is_authenticated:
            await self.close()
            return
        
        await self.accept()

        # 待機列(キャッシュ)を確認
        waiting_channel = await database_sync_to_async(cache.get)("waiting_player_channel")

        if waiting_channel:
            # --- 相手が見つかった場合 ---
            # 1. 待機情報を消す
            await database_sync_to_async(cache.delete)("waiting_player_channel")
            
            # 2. ランダムな部屋名を生成
            new_room_name = f"match_{uuid.uuid4().hex[:8]}"
            print(f"Match found! Room: {new_room_name}")

            # 3. 自分に通知 (JSでページ遷移させる)
            await self.send(text_data=json.dumps({
                'type': 'match_found',
                'room_name': new_room_name
            }))

            # 4. 待っていた相手に通知
            await self.channel_layer.send(
                waiting_channel,
                {
                    "type": "match.found.event",
                    "room_name": new_room_name,
                }
            )
        else:
            # --- 相手がいない場合 ---
            # 待機列に自分のチャンネル名を登録 (有効期限60秒)
            print("Waiting for opponent...")
            await database_sync_to_async(cache.set)("waiting_player_channel", self.channel_name, 60)
            await self.send(text_data=json.dumps({'type': 'waiting'}))

    async def disconnect(self, close_code):
        # 切断時、自分が待機中ならリストから消す
        my_channel = self.channel_name
        cached_channel = await database_sync_to_async(cache.get)("waiting_player_channel")
        if cached_channel == my_channel:
            await database_sync_to_async(cache.delete)("waiting_player_channel")

    # 相手が見つかったときのイベントハンドラ
    async def match_found_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'match_found',
            'room_name': event['room_name']
        }))


# ==========================================
# 2. ゲーム用コンシューマ (対戦 + レート機能)
# ==========================================
class TicTacToeConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'tictactoe_{self.room_name}'
        self.user = self.scope["user"]

        # ゲームロジックの初期化
        self.game = TicTacToe()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # 初期状態を送信
        await self.send(text_data=json.dumps(self._get_broadcast_data()))

        # 参加者の情報を全員に通知 (レート表示用)
        if self.user.is_authenticated:
            rating = await self.get_user_rating(self.user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'player_info_event',
                    'username': self.user.username,
                    'rating': rating
                }
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'move':
            # 手を打つ処理
            position = int(data.get('position'))
            # ※ここで「誰の手番か」などの厳密なチェックも可能ですが今回は省略
            result = self.game.make_move(position)

            if result['success']:
                # 勝敗判定
                game_state = self.game.get_state()
                if game_state['game_over'] and game_state['winner']:
                    # 勝者・敗者の特定 (簡易実装: 最後に打った人が勝者)
                    # 本来は player_id とユーザーを紐づける処理が必要
                    winner_user = self.user
                    # レート更新処理 (非同期DB操作)
                    # 注: 2人ともここを通るので重複処理しないよう工夫が必要ですが、
                    # 今回は「勝者側の通信」でのみ更新するようJS制御するか、サーバーでフラグ管理します。
                    # ここではシンプルに「勝った本人からの通信」として処理します。
                    pass # 具体的な更新は JS側からの 'game_over' 通知で行う形にしていましたね

        elif message_type == 'game_over_report':
            # ★クライアントから勝敗報告を受け取ってレート更新
            winner_name = data.get('winner_name')
            loser_name = data.get('loser_name')
            
            if winner_name and loser_name:
                new_ratings = await self.update_ratings(winner_name, loser_name)
                if new_ratings:
                    # 全員に新レートを通知
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'rating_update_event',
                            'ratings': new_ratings
                        }
                    )
        
        elif message_type == 'reset':
            self.game.reset()

        # 全員に盤面状態を配信
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_update_event',
                'message': self._get_broadcast_data()
            }
        )

    # --- イベントハンドラ ---
    async def game_update_event(self, event):
        await self.send(text_data=json.dumps(event['message']))

    async def player_info_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'player_joined',  # JS側で待っているtype
            'username': event['username'],
            'rating': event['rating']
        }))

    async def rating_update_event(self, event):
        await self.send(text_data=json.dumps({
            'type': 'rating_update',
            'ratings': event['ratings']
        }))

    # --- ヘルパーメソッド ---
    def _get_broadcast_data(self):
        state = self.game.get_state()
        winning_line = None
        if state['game_over']:
            try:
                winning_line = get_winning_line(state['board'])
            except:
                pass
        
        return {
            'type': 'game_state',
            'board': state['board'],
            'current_player': state['current_player'],
            'game_over': state['game_over'],
            'winner': state['winner'],
            'winning_line': winning_line
        }

    # --- DB操作 (同期関数を非同期化) ---
    @database_sync_to_async
    def get_user_rating(self, user):
        from team6.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=user)
        return profile.rating

    @database_sync_to_async
    def update_ratings(self, winner_name, loser_name):
        from team6.models import UserProfile
        try:
            w_prof = UserProfile.objects.get(user__username=winner_name)
            l_prof = UserProfile.objects.get(user__username=loser_name)
            
            # レート変動
            w_prof.rating += 20
            l_prof.rating -= 20
            w_prof.save()
            l_prof.save()
            
            return {
                winner_name: w_prof.rating,
                loser_name: l_prof.rating
            }
        except Exception as e:
            print(f"Rating update error: {e}")
            return None