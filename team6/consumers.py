import json
import uuid
import hashlib
import random
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from django.contrib.auth.models import User
from .models import UserProfile
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
        # 修正ポイント: 日本語のルーム名を英数字のハッシュ値に変換する
        # unicodeのルーム名を直接使うとエラーになるため、sha256などで英数字のみの文字列にする
        room_hash = hashlib.sha256(self.room_name.encode('utf-8')).hexdigest()[:32]
        self.room_group_name = f'tictactoe_{room_hash}'
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
                'player_wait': self.user.username, # 一時的に待機者として保存
                'player_x': self.user.username,
                'player_o': None,
                'game_over': False,
                'winner': None,
                'winning_line': [],
                'ratings_updated': False # レート二重更新防止フラグ
            }
        elif room_data['player_o'] is None and room_data['player_x'] != self.user.username:
            # 2人目が揃ったタイミングでランダムに割り振る
            players = [room_data.pop('player_wait'), self.user.username]
            random.shuffle(players) # 順番をシャッフル
            
            room_data['player_x'] = players[0] # 先行
            room_data['player_o'] = players[1] # 後攻

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

        if not room_data:
            return
        
        # サレンダー（自発的な離脱）の処理
        if data.get('type') == 'surrender':
            if not room_data['game_over']:
                # 自分を負け、相手を勝ちに設定
                is_me_x = (room_data['player_x'] == self.user.username)
                room_data['winner'] = 'O' if is_me_x else 'X'
                room_data['game_over'] = True

                # 終了理由を記録 (リロード時の対策)
                room_data['end_reason'] = 'retired'
                
                # レート更新
                if not room_data.get('ratings_updated'):
                    await self.handle_game_end_ratings(room_data)
                    room_data['ratings_updated'] = True
                
                await database_sync_to_async(cache.set)(room_key, room_data, 3600)

                # 相手に「離脱」イベントを通知 (自分を除外するために channel_name を付与)
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'opponent_retired_event',
                        'sender_channel_name': self.channel_name
                    }
                )

                # 通常のステート更新も送る (背景の盤面などを更新するため)
                await self.broadcast_state(room_data)
            return

        # リセット要求の処理
        if data.get('type') == 'reset':
            await self.handle_reset_request(room_data, room_key)
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

                # --- レート更新ロジックの追加 ---
                if room_data['game_over'] and not room_data.get('ratings_updated'):
                    await self.handle_game_end_ratings(room_data)
                    room_data['ratings_updated'] = True # 更新済みフラグを立てる

                await database_sync_to_async(cache.set)(room_key, room_data, 3600)
                await self.broadcast_state(room_data)

    async def disconnect(self, close_code):
        # ゲーム中の切断を敗北として扱う処理
        room_key = f"game_state_{self.room_name}"
        room_data = await database_sync_to_async(cache.get)(room_key)

        if room_data and not room_data['game_over'] and room_data['player_o'] is not None:
            # ゲーム中かつ2人揃っている状態で切断された場合
            is_me_x = (room_data['player_x'] == self.user.username)
            room_data['winner'] = 'O' if is_me_x else 'X'
            room_data['game_over'] = True

            # 終了理由を記録 (切断による終了)
            room_data['end_reason'] = 'retired'
            
            # レート更新
            if not room_data.get('ratings_updated'):
                await self.handle_game_end_ratings(room_data)
                room_data['ratings_updated'] = True
            
            await database_sync_to_async(cache.set)(room_key, room_data, 3600)
            
            # 残っている相手に通知を送信
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'opponent_retired_event'
                }
            )

        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # リタイアイベントのブロードキャスト用
    async def opponent_retired_event(self, event):
        if 'sender_channel_name' in event and event['sender_channel_name'] == self.channel_name:
            return

        await self.send(text_data=json.dumps({
            'type': 'opponent_retired'
        }))

    async def handle_reset_request(self, room_data, room_key):
        """リセット投票の管理"""
        # リセット希望者リストがなければ作成
        if 'reset_requested' not in room_data:
            room_data['reset_requested'] = []

        # すでにクリック済みの場合は何もしない
        if self.user.username in room_data['reset_requested']:
            return

        # リストに自分を追加
        room_data['reset_requested'].append(self.user.username)

        # 全員（2人）が揃ったかチェック
        if len(room_data['reset_requested']) >= 2:
            # ゲーム状態を初期化
            room_data.update({
                'board': [' ' for _ in range(9)],
                'current_player': 'X',
                'game_over': False,
                'winner': None,
                'winning_line': [],
                'ratings_updated': False,
                'reset_requested': [] # リストを空に戻す
            })
            await database_sync_to_async(cache.set)(room_key, room_data, 3600)
            await self.broadcast_state(room_data)
        else:
            # まだ1人目なら、キャッシュを更新して現在の状況を通知
            await database_sync_to_async(cache.set)(room_key, room_data, 3600)
            
            # クライアント側に「相手の同意待ち」であることを伝える通知（任意）
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'game_update_event',
                    'state': room_data
                }
            )

    async def handle_game_end_ratings(self, room_data):
        """勝敗に応じてレートを更新する"""
        winner = room_data['winner']
        p_x = room_data['player_x']
        p_o = room_data['player_o']

        # 二人揃っていない場合は更新しない
        if not p_x or not p_o:
            return

        if winner == 'X':
            await self.update_user_ratings(p_x, p_o, is_draw=False)
        elif winner == 'O':
            await self.update_user_ratings(p_o, p_x, is_draw=False)
        # 引き分けの場合は今回は変動なし（必要ならここに追加）

    @database_sync_to_async
    def update_user_ratings(self, winner_name, loser_name, is_draw=False):
        """データベースを操作してレートを増減させる"""
        try:
            winner_user = User.objects.get(username=winner_name)
            loser_user = User.objects.get(username=loser_name)
            
            w_profile = winner_user.profile
            l_profile = loser_user.profile

            if not is_draw:
                w_profile.rating += 16
                l_profile.rating -= 16
                # レートがマイナスにならないようにガード
                if l_profile.rating < 0:
                    l_profile.rating = 0
            
            w_profile.save()
            l_profile.save()
        except Exception as e:
            print(f"Rating update error: {e}")

    async def handle_reset(self):
        room_key = f"game_state_{self.room_name}"
        room_data = await database_sync_to_async(cache.get)(room_key)
        if room_data:
            room_data.update({
                'board': [' ' for _ in range(9)],
                'current_player': 'X',
                'game_over': False,
                'winner': None,
                'winning_line': [],
                'ratings_updated': False # リセット時はフラグも戻す
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

# team6/consumers.py の末尾に追記
from team6.game_logic.hitandblow import HitAndBlow

class HitAndBlowConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'hb_{self.room_name}'
        self.user = self.scope["user"]

        if not self.user.is_authenticated:
            await self.close()
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        room_key = f"hb_state_{self.room_name}"
        room_data = await database_sync_to_async(cache.get)(room_key)

        if not room_data:
            room_data = {
                'phase': 'setup', # setup or playing
                'player_x': self.user.username,
                'player_o': None,
                'secret_x': None,
                'secret_o': None,
                'current_turn': 'X',
                'history': [],
                'game_over': False
            }
        elif room_data['player_o'] is None and room_data['player_x'] != self.user.username:
            room_data['player_o'] = self.user.username
            # 二人揃った通知
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'game_event', 'message': {'type': 'system', 'text': '対戦相手が揃いました。秘密の3桁を設定してください。'}}
            )

        await database_sync_to_async(cache.set)(room_key, room_data, 3600)
        await self.broadcast_state(room_data)

    async def receive(self, text_data):
        data = json.loads(text_data)
        room_key = f"hb_state_{self.room_name}"
        room_data = await database_sync_to_async(cache.get)(room_key)

        if data['type'] == 'set_secret':
            # 秘密の数字を設定
            if self.user.username == room_data['player_x']:
                room_data['secret_x'] = data['value']
            else:
                room_data['secret_o'] = data['value']
            
            # 両方セット完了ならプレイ開始
            if room_data['secret_x'] and room_data['secret_o']:
                room_data['phase'] = 'playing'
            
            await database_sync_to_async(cache.set)(room_key, room_data, 3600)
            await self.broadcast_state(room_data)

        elif data['type'] == 'guess':
            # 回答フェーズ
            hb = HitAndBlow()
            guess = data['value']
            # XがOの数字を当てる、あるいはその逆
            is_x = (self.user.username == room_data['player_x'])
            secret = room_data['secret_o'] if is_x else room_data['secret_x']
            
            result = hb.calculate_result(secret, guess)
            history_item = {
                'user': self.user.username,
                'guess': "".join(map(str, guess)),
                'hit': result['hit'],
                'blow': result['blow']
            }
            room_data['history'].append(history_item)
            
            if result['hit'] == 3:
                room_data['game_over'] = True
                room_data['winner'] = self.user.username
            else:
                room_data['current_turn'] = 'O' if is_x else 'X'

            await database_sync_to_async(cache.set)(room_key, room_data, 3600)
            await self.broadcast_state(room_data)

    async def broadcast_state(self, room_data):
        # 秘密の数字そのものは送らないようにコピーを作成
        clean_data = room_data.copy()
        clean_data['secret_x_set'] = room_data['secret_x'] is not None
        clean_data['secret_o_set'] = room_data['secret_o'] is not None
        del clean_data['secret_x']
        del clean_data['secret_o']
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {'type': 'game_update', 'state': clean_data}
        )

    async def game_update(self, event):
        await self.send(text_data=json.dumps(event['state']))

    async def game_event(self, event):
        await self.send(text_data=json.dumps(event['message']))