"""
玩家类
管理玩家状态和行动
"""

from typing import Optional
from .hand import Hand

class Player:
    def __init__(self, name: str, chips: int = 1000, is_ai: bool = False):
        """
        初始化玩家

        Args:
            name: 玩家名称
            chips: 初始筹码数量
            is_ai: 是否为AI玩家
        """
        self.name = name
        self.chips = chips
        self.hand = Hand()
        self.bet_amount = 0
        self.is_active = True  # 是否还在游戏中（未弃牌）
        self.is_all_in = False  # 是否全押
        self.has_acted = False  # 在当前下注轮是否已行动
        self.is_dealer = False  # 是否为庄家
        self.is_small_blind = False  # 是否为小盲
        self.is_big_blind = False  # 是否为大盲
        self.is_ai = is_ai  # 是否为AI玩家

    def reset_for_new_hand(self):
        """为新的一手牌重置玩家状态"""
        self.hand.clear()
        self.bet_amount = 0
        self.is_active = True
        self.is_all_in = False
        self.has_acted = False
        self.is_dealer = False
        self.is_small_blind = False
        self.is_big_blind = False

    def place_bet(self, amount: int) -> int:
        """
        下注指定数量的筹码

        Args:
            amount: 要下注的筹码数量

        Returns:
            实际下注的筹码数量（可能因筹码不足而减少）

        Raises:
            ValueError: 如果下注金额为负数或超过玩家筹码
        """
        if amount < 0:
            raise ValueError("Bet amount cannot be negative")

        if amount > self.chips:
            raise ValueError(f"Cannot bet {amount}, only {self.chips} chips available")

        actual_bet = amount
        self.chips -= actual_bet
        self.bet_amount += actual_bet

        if self.chips == 0:
            self.is_all_in = True

        self.has_acted = True
        return actual_bet

    def call(self, current_bet: int) -> int:
        """
        跟注到当前下注额

        Args:
            current_bet: 当前轮次需要跟注的金额

        Returns:
            实际跟注的筹码数量
        """
        amount_to_call = current_bet - self.bet_amount

        if amount_to_call <= 0:
            # 已经下注足够，可以过牌
            self.has_acted = True
            return 0

        if amount_to_call >= self.chips:
            # 不够跟注，全押
            return self.all_in()

        return self.place_bet(amount_to_call)

    def raise_bet(self, current_bet: int, raise_amount: int) -> int:
        """
        加注

        Args:
            current_bet: 当前轮次需要跟注的金额
            raise_amount: 要加注的金额（在跟注基础上额外加注）

        Returns:
            实际下注的筹码数量
        """
        total_amount = (current_bet - self.bet_amount) + raise_amount

        if raise_amount < 0:
            raise ValueError("Raise amount cannot be negative")

        if total_amount > self.chips:
            # 不够加注，全押
            return self.all_in()

        return self.place_bet(total_amount)

    def all_in(self) -> int:
        """
        全押所有筹码

        Returns:
            全押的筹码数量
        """
        if self.chips == 0:
            self.has_acted = True
            return 0

        amount = self.chips
        self.place_bet(amount)
        self.is_all_in = True
        self.has_acted = True
        return amount

    def fold(self):
        """弃牌"""
        self.is_active = False
        self.has_acted = True

    def check(self):
        """过牌（如果不需要跟注）"""
        self.has_acted = True

    def collect_winnings(self, amount: int):
        """
        赢得筹码

        Args:
            amount: 赢得的筹码数量
        """
        self.chips += amount

    def get_amount_to_call(self, current_bet: int) -> int:
        """
        计算需要跟注的金额

        Args:
            current_bet: 当前轮次需要跟注的金额

        Returns:
            需要跟注的金额（如果为0或负数表示不需要跟注）
        """
        return current_bet - self.bet_amount

    def can_check(self, current_bet: int) -> bool:
        """检查是否可以过牌"""
        return self.get_amount_to_call(current_bet) <= 0

    def __str__(self):
        status_parts = []
        if not self.is_active:
            status_parts.append("FOLDED")
        if self.is_all_in:
            status_parts.append("ALL-IN")
        if self.is_dealer:
            status_parts.append("D")
        if self.is_small_blind:
            status_parts.append("SB")
        if self.is_big_blind:
            status_parts.append("BB")

        status_str = f" [{', '.join(status_parts)}]" if status_parts else ""

        return f"{self.name}: {self.chips} chips{status_str}"

    def __repr__(self):
        return f"Player(name='{self.name}', chips={self.chips}, active={self.is_active})"