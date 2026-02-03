"""
手牌类
管理玩家的两张底牌
"""

from typing import List
from .card import Card

class Hand:
    def __init__(self):
        """初始化空手牌"""
        self.cards = []

    def add_card(self, card: Card):
        """
        添加一张牌到手牌

        Args:
            card: 要添加的Card对象
        """
        if len(self.cards) >= 2:
            raise ValueError("A hand can only hold 2 cards")
        self.cards.append(card)

    def add_cards(self, cards: List[Card]):
        """
        添加多张牌到手牌

        Args:
            cards: Card对象列表
        """
        for card in cards:
            self.add_card(card)

    def clear(self):
        """清空手牌"""
        self.cards = []

    def get_cards(self):
        """获取手牌中的所有牌"""
        return self.cards.copy()

    def __len__(self):
        return len(self.cards)

    def __str__(self):
        if not self.cards:
            return "Empty hand"
        return " ".join(str(card) for card in self.cards)

    def __repr__(self):
        return f"Hand({self.cards})"

    def to_list(self):
        """转换为列表表示"""
        return [card.to_dict() for card in self.cards]

    @classmethod
    def from_list(cls, cards_data):
        """从列表创建Hand对象"""
        hand = cls()
        for card_data in cards_data:
            hand.add_card(Card.from_dict(card_data))
        return hand