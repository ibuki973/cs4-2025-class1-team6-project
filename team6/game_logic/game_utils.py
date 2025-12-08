"""
ゲーム共通のユーティリティ関数
"""

import json
from datetime import datetime


class GameState:
    """ゲームセッション管理用クラス"""
    
    def __init__(self, game_name, player1_id, player2_id, game_instance):
        """
        ゲームセッションを初期化
        
        Args:
            game_name (str): ゲーム名（例：'tictactoe'）
            player1_id (int): プレイヤー1のユーザーID
            player2_id (int): プレイヤー2のユーザーID
            game_instance: ゲームロジックのインスタンス
        """
        self.game_name = game_name
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.game = game_instance
        self.created_at = datetime.now()
        self.completed_at = None
    
    def to_dict(self):
        """セッション情報を辞書に変換"""
        return {
            'game_name': self.game_name,
            'player1_id': self.player1_id,
            'player2_id': self.player2_id,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'game_state': self.game.get_state()
        }


def validate_player_move(board, position):
    """
    プレイヤーの移動が有効かチェック
    
    Args:
        board (list): 9要素のボード
        position (int): 0-8の位置
        
    Returns:
        bool: 有効ならTrue
    """
    if not isinstance(position, int) or position < 0 or position > 8:
        return False
    return board[position] == ' '


def get_winning_line(board):
    """
    勝ちパターンを取得
    
    Args:
        board (list): 9要素のボード
        
    Returns:
        list: 勝ちパターンのインデックス（勝者がいなければNone）
    """
    winning_positions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # 行
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # 列
        [0, 4, 8], [2, 4, 6]              # 対角線
    ]
    
    for positions in winning_positions:
        a, b, c = positions
        if (board[a] != ' ' and 
            board[a] == board[b] == board[c]):
            return positions
    
    return None


def serialize_game_data(game_state):
    """
    ゲーム状態をJSON送信用にシリアライズ
    
    Args:
        game_state (dict): ゲーム状態辞書
        
    Returns:
        str: JSON文字列
    """
    return json.dumps(game_state, ensure_ascii=False, indent=2)


def deserialize_game_data(json_str):
    """
    JSON文字列をゲーム状態に逆シリアライズ
    
    Args:
        json_str (str): JSON文字列
        
    Returns:
        dict: ゲーム状態辞書
    """
    return json.loads(json_str)
"""
ゲーム共通のユーティリティ関数
"""

import json
from datetime import datetime


class GameState:
    """ゲームセッション管理用クラス"""
    
    def __init__(self, game_name, player1_id, player2_id, game_instance):
        """
        ゲームセッションを初期化
        
        Args:
            game_name (str): ゲーム名（例：'tictactoe'）
            player1_id (int): プレイヤー1のユーザーID
            player2_id (int): プレイヤー2のユーザーID
            game_instance: ゲームロジックのインスタンス
        """
        self.game_name = game_name
        self.player1_id = player1_id
        self.player2_id = player2_id
        self.game = game_instance
        self.created_at = datetime.now()
        self.completed_at = None
    
    def to_dict(self):
        """セッション情報を辞書に変換"""
        return {
            'game_name': self.game_name,
            'player1_id': self.player1_id,
            'player2_id': self.player2_id,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'game_state': self.game.get_state()
        }


def validate_player_move(board, position):
    """
    プレイヤーの移動が有効かチェック
    
    Args:
        board (list): 9要素のボード
        position (int): 0-8の位置
        
    Returns:
        bool: 有効ならTrue
    """
    if not isinstance(position, int) or position < 0 or position > 8:
        return False
    return board[position] == ' '


def get_winning_line(board):
    """
    勝ちパターンを取得
    
    Args:
        board (list): 9要素のボード
        
    Returns:
        list: 勝ちパターンのインデックス（勝者がいなければNone）
    """
    winning_positions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],  # 行
        [0, 3, 6], [1, 4, 7], [2, 5, 8],  # 列
        [0, 4, 8], [2, 4, 6]              # 対角線
    ]
    
    for positions in winning_positions:
        a, b, c = positions
        if (board[a] != ' ' and 
            board[a] == board[b] == board[c]):
            return positions
    
    return None


def serialize_game_data(game_state):
    """
    ゲーム状態をJSON送信用にシリアライズ
    
    Args:
        game_state (dict): ゲーム状態辞書
        
    Returns:
        str: JSON文字列
    """
    return json.dumps(game_state, ensure_ascii=False, indent=2)


def deserialize_game_data(json_str):
    """
    JSON文字列をゲーム状態に逆シリアライズ
    
    Args:
        json_str (str): JSON文字列
        
    Returns:
        dict: ゲーム状態辞書
    """
    return json.loads(json_str)
