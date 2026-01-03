class ECard:
    # カードの種類
    EMPEROR = 'E'  # 皇帝
    SLAVE = 'S'    # 奴隷
    CITIZEN = 'C'  # 市民

    def __init__(self):
        self.reset()

    def reset(self):
        self.p1_cards = [self.EMPEROR, self.CITIZEN, self.CITIZEN, self.CITIZEN, self.CITIZEN]
        self.p2_cards = [self.SLAVE, self.CITIZEN, self.CITIZEN, self.CITIZEN, self.CITIZEN]
        self.winner = None

    @staticmethod
    def judge(card1, card2):
        """
        P1のカード(card1)とP2のカード(card2)を比較
        戻り値: 1(P1勝), 2(P2勝), 0(引き分け)
        """
        if card1 == card2:
            return 0
        # 皇帝 vs 市民 -> 皇帝(P1)勝
        if card1 == 'E' and card2 == 'C': return 1
        # 市民 vs 奴隷 -> 市民(P1)勝
        if card1 == 'C' and card2 == 'S': return 1
        # 奴隷 vs 皇帝 -> 奴隷(P2)勝
        if card1 == 'S' and card2 == 'E': return 2
        # その他（皇帝 vs 奴隷 など）
        if card1 == 'E' and card2 == 'S': return 2
        if card1 == 'C' and card2 == 'E': return 2
        if card1 == 'S' and card2 == 'C': return 2
        return 0