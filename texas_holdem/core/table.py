"""
牌桌类
管理公共牌、底池和边池
"""

from typing import List, Dict, Tuple
from .card import Card

class Pot:
    """底池类"""
    def __init__(self, amount: int = 0):
        self.amount = amount
        self.eligible_players = set()  # 有资格赢得此底池的玩家

    def add(self, amount: int):
        """向底池添加筹码"""
        self.amount += amount

    def reset(self):
        """重置底池"""
        self.amount = 0
        self.eligible_players.clear()

    def __str__(self):
        return f"Pot({self.amount})"

class SidePot(Pot):
    """边池类"""
    def __init__(self, amount: int = 0, max_contribution: int = 0):
        super().__init__(amount)
        self.max_contribution = max_contribution  # 玩家在此边池的最大贡献

class Table:
    def __init__(self):
        """初始化牌桌"""
        self.community_cards = []
        self.main_pot = Pot()
        self.side_pots = []
        self.total_pot = 0

    def reset(self):
        """重置牌桌状态（开始新的一手牌）"""
        self.community_cards.clear()
        self.main_pot.reset()
        self.side_pots.clear()
        self.total_pot = 0

    def add_community_card(self, card: Card):
        """
        添加一张公共牌

        Args:
            card: 要添加的Card对象
        """
        if len(self.community_cards) >= 5:
            raise ValueError("Cannot add more than 5 community cards")
        self.community_cards.append(card)

    def add_community_cards(self, cards: List[Card]):
        """
        添加多张公共牌

        Args:
            cards: Card对象列表
        """
        for card in cards:
            self.add_community_card(card)

    def get_community_cards(self):
        """获取所有公共牌"""
        return self.community_cards.copy()

    def get_flop(self):
        """获取翻牌（前3张公共牌）"""
        return self.community_cards[:3] if len(self.community_cards) >= 3 else []

    def get_turn(self):
        """获取转牌（第4张公共牌）"""
        return self.community_cards[3] if len(self.community_cards) >= 4 else None

    def get_river(self):
        """获取河牌（第5张公共牌）"""
        return self.community_cards[4] if len(self.community_cards) >= 5 else None

    def collect_bets(self, players):
        """
        收集所有玩家的下注到底池
        注意：底池是累积的，不会重置之前轮次的下注

        Args:
            players: 玩家列表

        Returns:
            创建的边池列表
        """
        # 计算每个玩家的总下注（本轮新增）
        player_bets = {player: player.bet_amount for player in players if player.bet_amount > 0}

        if not player_bets:
            return []

        # 按总下注额排序
        sorted_bets = sorted(set(player_bets.values()))
        all_in_amounts = [amt for amt in sorted_bets if amt > 0]

        # 注意：不清空主池和边池，底池是累积的
        # 只在没有边池的情况下处理（简化版本）
        # 如果有复杂的全押边池情况，需要更复杂的逻辑

        prev_amount = 0
        side_pots_created = []

        for amount in all_in_amounts:
            # 计算当前层的贡献
            layer_amount = amount - prev_amount

            # 计算当前层有多少玩家有资格
            eligible_players = [p for p, bet in player_bets.items() if bet >= amount]

            if prev_amount == 0:
                # 第一层是主池
                pot = self.main_pot
            else:
                # 后续层是边池
                pot = SidePot(max_contribution=layer_amount)
                self.side_pots.append(pot)
                side_pots_created.append(pot)

            pot.eligible_players.update(eligible_players)

            # 计算总筹码量
            total_in_layer = layer_amount * len(eligible_players)
            pot.add(total_in_layer)

            prev_amount = amount

        # 更新总底池金额
        self.total_pot = self.main_pot.amount + sum(pot.amount for pot in self.side_pots)

        # 重置玩家的下注金额
        for player in players:
            player.bet_amount = 0

        return side_pots_created

    def award_pots(self, winners_by_pot):
        """
        分配底池给赢家

        Args:
            winners_by_pot: 字典，键为底池对象，值为赢家列表

        Returns:
            每个玩家赢得的筹码数量字典
        """
        winnings = {}

        # 分配主池
        if self.main_pot in winners_by_pot:
            winners = winners_by_pot[self.main_pot]
            if winners:
                share = self.main_pot.amount // len(winners)
                remainder = self.main_pot.amount % len(winners)

                for i, winner in enumerate(winners):
                    amount = share + (1 if i < remainder else 0)
                    winnings[winner] = winnings.get(winner, 0) + amount

        # 分配边池
        for side_pot in self.side_pots:
            if side_pot in winners_by_pot:
                winners = winners_by_pot[side_pot]
                if winners:
                    share = side_pot.amount // len(winners)
                    remainder = side_pot.amount % len(winners)

                    for i, winner in enumerate(winners):
                        amount = share + (1 if i < remainder else 0)
                        winnings[winner] = winnings.get(winner, 0) + amount

        return winnings

    def __str__(self):
        community_str = " ".join(str(card) for card in self.community_cards) if self.community_cards else "No community cards"
        pots_str = f"Main pot: {self.main_pot.amount}"

        if self.side_pots:
            pots_str += f", Side pots: {[pot.amount for pot in self.side_pots]}"

        return f"Table: {community_str} | Total pot: {self.total_pot} | {pots_str}"