#!/usr/bin/env python3
"""
简单测试游戏是否能运行
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 测试Card类
try:
    from core.card import Card
except ImportError:
    from texas_holdem.core.card import Card

# 创建一些Card对象
print("测试Card类...")
c1 = Card('H', 'A')
c2 = Card('D', 'K')
c3 = Card('H', 'A')  # 与c1相同

print(f"c1: {c1}, value: {c1.value}")
print(f"c2: {c2}, value: {c2.value}")
print(f"c3: {c3}, value: {c3.value}")

# 测试比较
print(f"c1 < c2: {c1 < c2}")
print(f"c1 > c2: {c1 > c2}")
print(f"c1 == c3: {c1 == c3}")

# 测试排序
cards = [c2, c1, Card('C', 'Q'), Card('S', '10')]
print(f"排序前: {cards}")
try:
    cards.sort(reverse=True)
    print(f"排序后: {cards}")
except Exception as e:
    print(f"排序错误: {e}")

# 测试评估器
print("\n测试评估器...")
try:
    from core.evaluator import PokerEvaluator

    # 测试手牌评估
    test_cards = [
        Card('H', 'A'),
        Card('D', 'A'),
        Card('H', 'K'),
        Card('D', 'K'),
        Card('H', 'Q'),
        Card('D', 'Q'),
        Card('H', 'J')
    ]

    rank, values = PokerEvaluator.evaluate_hand(test_cards)
    print(f"手牌等级: {rank}, 值: {values}")

except Exception as e:
    print(f"评估器错误: {e}")
    import traceback
    traceback.print_exc()

print("\n测试完成!")