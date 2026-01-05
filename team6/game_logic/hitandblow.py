import random

class HitAndBlow:
    """3桁のヒット・アンド・ブロー判定ロジック"""
    def __init__(self, digits=3):
        self.digits = digits

    def calculate_result(self, secret, guess):
        """
        secret: 正解のリスト (例: [1, 2, 3])
        guess: 予想のリスト (例: [1, 3, 5])
        戻り値: {'hit': 数, 'blow': 数}
        """
        hit = 0
        blow = 0
        for i in range(self.digits):
            if guess[i] == secret[i]:
                hit += 1
            elif guess[i] in secret:
                blow += 1
        return {'hit': hit, 'blow': blow}

    def is_valid_input(self, input_list):
        """入力が有効か（桁数、重複なし、数字のみ）をチェック"""
        if len(input_list) != self.digits:
            return False
        if len(set(input_list)) != self.digits:
            return False
        return all(0 <= x <= 9 for x in input_list)