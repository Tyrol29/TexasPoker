#!/usr/bin/env python3
"""
测试增强的AI功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from ui.cli import CLI
except ImportError:
    # 尝试直接导入
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from texas_holdem.ui.cli import CLI

def test_monte_carlo():
    """测试蒙特卡洛胜率计算"""
    cli = CLI()

    # 导入Card类
    try:
        from core.card import Card
    except ImportError:
        from texas_holdem.core.card import Card

    # 测试手牌：口袋A
    # Card构造函数：Card(suit, rank) 其中suit是'H','D','C','S'，rank是'2'-'10','J','Q','K','A'
    hole_cards = [Card('H', 'A'), Card('D', 'A')]  # 两张A，不同花色

    # 测试不同公共牌情况
    test_cases = [
        ([], "翻牌前"),
        ([Card('H', '10'), Card('H', 'J'), Card('H', 'Q')], "翻牌圈"),
        ([Card('H', '10'), Card('H', 'J'), Card('H', 'Q'), Card('D', '2')], "转牌圈"),
        ([Card('H', '10'), Card('H', 'J'), Card('H', 'Q'), Card('D', '2'), Card('C', '3')], "河牌圈")
    ]

    print("测试蒙特卡洛胜率计算:")
    print("-" * 50)

    for community_cards, desc in test_cases:
        equity = cli._calculate_equity_monte_carlo(hole_cards, community_cards, iterations=500)
        print(f"{desc}: 胜率 = {equity:.2%}")

    print("\n测试Outs计算:")
    print("-" * 50)

    # 测试同花听牌
    hole_cards2 = [Card('H', 'A'), Card('H', 'K')]  # 同花A K
    community_cards2 = [Card('H', '10'), Card('H', '5'), Card('D', '2')]  # 翻牌，两张同花

    outs_info = cli._calculate_outs(hole_cards2, community_cards2)
    print(f"同花听牌: {outs_info}")

    # 测试顺子听牌
    hole_cards3 = [Card('H', '8'), Card('D', '9')]
    community_cards3 = [Card('C', '10'), Card('S', '7'), Card('H', '2')]

    outs_info2 = cli._calculate_outs(hole_cards3, community_cards3)
    print(f"顺子听牌: {outs_info2}")

def test_opponent_stats():
    """测试对手统计"""
    cli = CLI()

    try:
        from core.player import Player
    except ImportError:
        from texas_holdem.core.player import Player

    # 创建测试玩家
    players = [
        Player("AI", 1000, is_ai=True),
        Player("Human", 1000, is_ai=False)
    ]

    # 初始化统计
    cli._initialize_opponent_stats(players)

    print("\n测试对手统计:")
    print("-" * 50)
    print("初始统计:", cli.opponent_stats)

    # 更新一些统计
    cli._update_opponent_stats("Human", "raise", "preflop", 50)
    cli._update_opponent_stats("Human", "call", "flop", 20)

    print("更新后统计:", cli.opponent_stats)

    # 获取倾向分析
    tendency = cli._get_opponent_tendency("Human")
    print("对手倾向:", tendency)

def test_win_probability():
    """测试胜率估算"""
    cli = CLI()

    try:
        from core.card import Card
    except ImportError:
        from texas_holdem.core.card import Card

    hole_cards = [Card('H', 'A'), Card('D', 'A')]  # 口袋A

    test_cases = [
        ([], "翻牌前"),
        ([Card('H', '10'), Card('H', 'J'), Card('H', 'Q')], "翻牌圈"),
        ([Card('H', '10'), Card('H', 'J'), Card('H', 'Q'), Card('D', '2')], "转牌圈"),
    ]

    print("\n测试胜率估算:")
    print("-" * 50)

    for community_cards, desc in test_cases:
        win_prob = cli._estimate_win_probability(hole_cards, community_cards)
        print(f"{desc}: 胜率 = {win_prob:.2%}")

if __name__ == "__main__":
    print("德州扑克AI增强功能测试")
    print("=" * 60)

    try:
        test_monte_carlo()
        test_opponent_stats()
        test_win_probability()

        print("\n所有测试完成!")

    except Exception as e:
        print(f"测试出错: {e}")
        import traceback
        traceback.print_exc()