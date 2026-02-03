"""
手牌评估器
评估德州扑克手牌的强度和牌型
"""

import itertools
from typing import List, Tuple, Dict, Optional
from .card import Card

class PokerEvaluator:
    """德州扑克手牌评估器"""

    # 手牌等级常量
    HIGH_CARD = 0
    ONE_PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8
    ROYAL_FLUSH = 9

    # 等级名称映射
    HAND_RANK_NAMES = {
        HIGH_CARD: "高牌",
        ONE_PAIR: "一对",
        TWO_PAIR: "两对",
        THREE_OF_A_KIND: "三条",
        STRAIGHT: "顺子",
        FLUSH: "同花",
        FULL_HOUSE: "葫芦",
        FOUR_OF_A_KIND: "四条",
        STRAIGHT_FLUSH: "同花顺",
        ROYAL_FLUSH: "皇家同花顺"
    }

    @staticmethod
    def evaluate_hand(cards: List[Card]) -> Tuple[int, List[int]]:
        """
        评估7张牌中的最佳5张牌组合

        Args:
            cards: 7张牌的列表（2张底牌 + 5张公共牌）

        Returns:
            (hand_rank, rank_values) 元组
            hand_rank: 手牌等级（0-9）
            rank_values: 用于比较的牌面值列表（从高到低排序）
        """
        if len(cards) < 5:
            raise ValueError(f"Need at least 5 cards, got {len(cards)}")

        # 生成所有5张牌的组合
        best_rank = -1
        best_rank_values = []

        for combo in itertools.combinations(cards, 5):
            rank, rank_values = PokerEvaluator._evaluate_five_card_hand(list(combo))
            if rank > best_rank or (rank == best_rank and rank_values > best_rank_values):
                best_rank = rank
                best_rank_values = rank_values

        return best_rank, best_rank_values

    @staticmethod
    def _evaluate_five_card_hand(cards: List[Card]) -> Tuple[int, List[int]]:
        """
        评估5张牌的手牌

        Args:
            cards: 5张牌的列表

        Returns:
            (hand_rank, rank_values) 元组
        """
        # 按牌面值排序（从高到低）
        cards.sort(reverse=True)
        values = [card.value for card in cards]
        suits = [card.suit for card in cards]

        # 检查是否为同花
        is_flush = len(set(suits)) == 1

        # 检查是否为顺子
        is_straight = False
        straight_high = 0

        # 处理A可以当作1的特殊情况
        value_set = set(values)
        if 14 in value_set:  # 有A
            value_set.add(1)  # 添加A作为1的情况

        sorted_values = sorted(value_set, reverse=True)

        # 检查顺子
        for i in range(len(sorted_values) - 4):
            if sorted_values[i] - sorted_values[i + 4] == 4:
                is_straight = True
                straight_high = sorted_values[i]
                break

        # 特殊处理5-high顺子 (A-2-3-4-5)
        if {14, 2, 3, 4, 5}.issubset(value_set):
            is_straight = True
            straight_high = 5

        # 皇家同花顺
        if is_flush and is_straight and straight_high == 14:
            return PokerEvaluator.ROYAL_FLUSH, [14]

        # 同花顺
        if is_flush and is_straight:
            return PokerEvaluator.STRAIGHT_FLUSH, [straight_high]

        # 统计牌面值频率
        value_counts = {}
        for value in values:
            value_counts[value] = value_counts.get(value, 0) + 1

        # 按频率和牌面值排序
        sorted_counts = sorted(value_counts.items(), key=lambda x: (-x[1], -x[0]))

        # 提取牌面值用于比较
        kickers = [value for value, count in sorted_counts]

        # 四条
        if sorted_counts[0][1] == 4:
            four_value = sorted_counts[0][0]
            kicker = sorted_counts[1][0]
            return PokerEvaluator.FOUR_OF_A_KIND, [four_value, kicker]

        # 葫芦
        if sorted_counts[0][1] == 3 and sorted_counts[1][1] >= 2:
            three_value = sorted_counts[0][0]
            pair_value = sorted_counts[1][0]
            return PokerEvaluator.FULL_HOUSE, [three_value, pair_value]

        # 同花
        if is_flush:
            return PokerEvaluator.FLUSH, values

        # 顺子
        if is_straight:
            return PokerEvaluator.STRAIGHT, [straight_high]

        # 三条
        if sorted_counts[0][1] == 3:
            three_value = sorted_counts[0][0]
            other_values = [value for value, count in sorted_counts[1:]]
            return PokerEvaluator.THREE_OF_A_KIND, [three_value] + other_values[:2]

        # 两对
        if sorted_counts[0][1] == 2 and sorted_counts[1][1] == 2:
            pair1_value = sorted_counts[0][0]
            pair2_value = sorted_counts[1][0]
            kicker = sorted_counts[2][0]
            return PokerEvaluator.TWO_PAIR, [max(pair1_value, pair2_value),
                                             min(pair1_value, pair2_value),
                                             kicker]

        # 一对
        if sorted_counts[0][1] == 2:
            pair_value = sorted_counts[0][0]
            other_values = [value for value, count in sorted_counts[1:]]
            return PokerEvaluator.ONE_PAIR, [pair_value] + other_values[:3]

        # 高牌
        return PokerEvaluator.HIGH_CARD, values[:5]

    @staticmethod
    def compare_hands(hand1_cards: List[Card], hand2_cards: List[Card]) -> int:
        """
        比较两手牌的强弱

        Args:
            hand1_cards: 玩家1的7张牌
            hand2_cards: 玩家2的7张牌

        Returns:
            1: hand1更强
            -1: hand2更强
            0: 平局
        """
        rank1, values1 = PokerEvaluator.evaluate_hand(hand1_cards)
        rank2, values2 = PokerEvaluator.evaluate_hand(hand2_cards)

        if rank1 > rank2:
            return 1
        elif rank1 < rank2:
            return -1
        else:
            # 相同牌型，比较牌面值
            for v1, v2 in zip(values1, values2):
                if v1 > v2:
                    return 1
                elif v1 < v2:
                    return -1
            return 0

    @staticmethod
    def get_hand_name(hand_rank: int) -> str:
        """获取手牌等级名称"""
        return PokerEvaluator.HAND_RANK_NAMES.get(hand_rank, "未知牌型")

    @staticmethod
    def get_best_hand_description(cards: List[Card]) -> str:
        """
        获取最佳手牌的描述

        Args:
            cards: 7张牌的列表

        Returns:
            手牌描述字符串
        """
        rank, values = PokerEvaluator.evaluate_hand(cards)
        hand_name = PokerEvaluator.get_hand_name(rank)

        # 添加具体的牌面值信息
        if rank == PokerEvaluator.HIGH_CARD:
            high_card = Card.RANK_TO_STR.get(values[0], str(values[0]))
            return f"{hand_name} ({high_card}高)"

        elif rank == PokerEvaluator.ONE_PAIR:
            pair_value = Card.RANK_TO_STR.get(values[0], str(values[0]))
            kickers = [Card.RANK_TO_STR.get(v, str(v)) for v in values[1:]]
            return f"{hand_name} {pair_value}s (踢脚 {', '.join(kickers)})"

        elif rank == PokerEvaluator.TWO_PAIR:
            pair1 = Card.RANK_TO_STR.get(values[0], str(values[0]))
            pair2 = Card.RANK_TO_STR.get(values[1], str(values[1]))
            kicker = Card.RANK_TO_STR.get(values[2], str(values[2]))
            return f"{hand_name} {pair1}s和{pair2}s (踢脚 {kicker})"

        elif rank == PokerEvaluator.THREE_OF_A_KIND:
            three_value = Card.RANK_TO_STR.get(values[0], str(values[0]))
            return f"{hand_name} {three_value}s"

        elif rank == PokerEvaluator.STRAIGHT:
            high_value = Card.RANK_TO_STR.get(values[0], str(values[0]))
            return f"{hand_name}到{high_value}"

        elif rank == PokerEvaluator.FLUSH:
            high_value = Card.RANK_TO_STR.get(values[0], str(values[0]))
            return f"{hand_name} {high_value}高"

        elif rank == PokerEvaluator.FULL_HOUSE:
            three_value = Card.RANK_TO_STR.get(values[0], str(values[0]))
            pair_value = Card.RANK_TO_STR.get(values[1], str(values[1]))
            return f"{hand_name} {three_value}s盖{pair_value}s"

        elif rank == PokerEvaluator.FOUR_OF_A_KIND:
            four_value = Card.RANK_TO_STR.get(values[0], str(values[0]))
            kicker = Card.RANK_TO_STR.get(values[1], str(values[1]))
            return f"{hand_name} {four_value}s (踢脚 {kicker})"

        elif rank == PokerEvaluator.STRAIGHT_FLUSH:
            high_value = Card.RANK_TO_STR.get(values[0], str(values[0]))
            return f"{hand_name}到{high_value}"

        elif rank == PokerEvaluator.ROYAL_FLUSH:
            return hand_name

        return hand_name