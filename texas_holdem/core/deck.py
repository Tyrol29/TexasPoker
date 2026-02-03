"""
牌组类
管理一副52张的标准扑克牌
"""

import random
from .card import Card

class Deck:
    def __init__(self):
        """初始化一副完整的52张扑克牌"""
        self.cards = []
        self.reset()

    def reset(self):
        """重置牌组为完整的52张牌"""
        self.cards = []
        suits = ['H', 'D', 'C', 'S']  # 红桃、方块、梅花、黑桃
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']

        for suit in suits:
            for rank in ranks:
                self.cards.append(Card(suit, rank))

    def shuffle(self):
        """随机洗牌"""
        random.shuffle(self.cards)

    def draw(self, count=1):
        """
        从牌组顶部抽取指定数量的牌

        Args:
            count: 要抽取的牌数量

        Returns:
            如果count=1，返回单张Card对象；否则返回Card对象列表
        """
        if count > len(self.cards):
            raise ValueError(f"Cannot draw {count} cards, only {len(self.cards)} remaining")

        drawn = self.cards[:count]
        self.cards = self.cards[count:]

        return drawn[0] if count == 1 else drawn

    def remaining(self):
        """返回剩余牌的数量"""
        return len(self.cards)

    def __len__(self):
        return len(self.cards)

    def __str__(self):
        return f"Deck with {len(self.cards)} cards"

    def peek(self, count=1):
        """
        查看牌组顶部的牌但不抽取

        Args:
            count: 要查看的牌数量

        Returns:
            Card对象列表
        """
        if count > len(self.cards):
            raise ValueError(f"Cannot peek {count} cards, only {len(self.cards)} remaining")
        return self.cards[:count]