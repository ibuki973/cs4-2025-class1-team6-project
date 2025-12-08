"""
三目並べ（Tic Tac Toe）ゲームロジック
"""

class TicTacToe:
    """
    3×3の三目並べゲーム
    
    Attributes:
        board (list): 3×3のゲームボード（0-8のインデックス）
        current_player (str): 現在のプレイヤー ('X' または 'O')
        game_over (bool): ゲーム終了フラグ
        winner (str): 勝者 ('X', 'O', 'draw', None)
    """
    
    def __init__(self):
        """ゲームを初期化"""
        self.board = [' ' for _ in range(9)]  # 空のボード
        self.current_player = 'X'  # Xから開始
        self.game_over = False
        self.winner = None
        self.move_history = []  # ゲーム進行の履歴
    
    def is_valid_move(self, position):
        """
        指定位置に移動可能かチェック
        
        Args:
            position (int): 0-8のボード位置
            
        Returns:
            bool: 有効な移動ならTrue
        """
        if not isinstance(position, int) or position < 0 or position > 8:
            return False
        return self.board[position] == ' '
    
    def make_move(self, position):
        """
        プレイヤーが移動を実行
        
        Args:
            position (int): 0-8のボード位置
            
        Returns:
            dict: {
                'success': bool,
                'message': str,
                'board': list,
                'current_player': str,
                'game_over': bool,
                'winner': str or None
            }
        """
        if self.game_over:
            return {
                'success': False,
                'message': 'ゲームは終了しています',
                'board': self.board,
                'game_over': True,
                'winner': self.winner
            }
        
        if not self.is_valid_move(position):
            return {
                'success': False,
                'message': '無効な移動です',
                'board': self.board,
                'current_player': self.current_player,
                'game_over': False,
                'winner': None
            }
        
        # ボードに配置
        self.board[position] = self.current_player
        self.move_history.append({
            'player': self.current_player,
            'position': position
        })
        
        # 勝敗判定
        winner = self._check_winner()
        
        if winner:
            self.game_over = True
            self.winner = winner
            return {
                'success': True,
                'message': f'プレイヤー {winner} が勝ちました！',
                'board': self.board,
                'game_over': True,
                'winner': winner
            }
        
        # 引き分け判定
        if self._is_board_full():
            self.game_over = True
            self.winner = 'draw'
            return {
                'success': True,
                'message': '引き分けです',
                'board': self.board,
                'game_over': True,
                'winner': 'draw'
            }
        
        # プレイヤーを切り替え
        self.current_player = 'O' if self.current_player == 'X' else 'X'
        
        return {
            'success': True,
            'message': f'プレイヤー {self.current_player} のターン',
            'board': self.board,
            'current_player': self.current_player,
            'game_over': False,
            'winner': None
        }
    
    def _check_winner(self):
        """
        勝者をチェック
        
        Returns:
            str: 'X', 'O', またはNone
        """
        # 勝ちパターン（行、列、対角線）
        winning_positions = [
            # 行
            [0, 1, 2],
            [3, 4, 5],
            [6, 7, 8],
            # 列
            [0, 3, 6],
            [1, 4, 7],
            [2, 5, 8],
            # 対角線
            [0, 4, 8],
            [2, 4, 6]
        ]
        
        for positions in winning_positions:
            a, b, c = positions
            if (self.board[a] != ' ' and 
                self.board[a] == self.board[b] == self.board[c]):
                return self.board[a]
        
        return None
    
    def _is_board_full(self):
        """ボードが満杯かチェック"""
        return ' ' not in self.board
    
    def get_state(self):
        """
        現在のゲーム状態を辞書で返す
        
        Returns:
            dict: ゲーム状態
        """
        return {
            'board': self.board,
            'current_player': self.current_player,
            'game_over': self.game_over,
            'winner': self.winner,
            'board_full': self._is_board_full(),
            'move_history': self.move_history
        }
    
    def reset(self):
        """ゲームをリセット"""
        self.__init__()
    
    @staticmethod
    def board_to_display(board):
        """
        ボード状態を表示用フォーマットに変換
        
        Args:
            board (list): 9要素のボード
            
        Returns:
            str: 表示用文字列
        """
        display = "\n"
        for i in range(3):
            row = board[i*3:(i+1)*3]
            display += f" {row[0]} | {row[1]} | {row[2]} \n"
            if i < 2:
                display += "-----------\n"
        return display
