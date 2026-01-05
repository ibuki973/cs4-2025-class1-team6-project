class ECard:
    EMPEROR = 'E'
    CITIZEN = 'C'
    SLAVE = 'S'

    @staticmethod
    def judge(card_emp, card_slv):
        """
        第1引数: 皇帝側のカード, 第2引数: 奴隷側のカード
        戻り値: (結果メッセージ, 勝利サイド, ゲーム終了フラグ)
        """
        # 1. 皇帝 vs 奴隷 (奴隷の逆転勝利)
        if card_emp == 'E' and card_slv == 'S':
            return "奴隷が皇帝を討ち取った！", 'slave_side', True
        
        # 2. 皇帝 vs 市民 (皇帝の勝利)
        if card_emp == 'E' and card_slv == 'C':
            return "皇帝の勝利！", 'emperor_side', True
        
        # 3. 市民 vs 奴隷 (市民の勝利)
        if card_emp == 'C' and card_slv == 'S':
            return "市民の勝利（皇帝側の守り）！", 'emperor_side', True
        
        # 4. 市民 vs 市民 (引き分け・継続)
        return "市民同士、引き分け...", None, False