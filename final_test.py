#!/usr/bin/env python3
"""
最终功能验证测试
"""

import sys
sys.path.insert(0, '.')

def test_imports():
    """测试所有模块导入"""
    print("测试模块导入...")

    modules = [
        "texas_holdem.core.card",
        "texas_holdem.core.deck",
        "texas_holdem.core.hand",
        "texas_holdem.core.player",
        "texas_holdem.core.table",
        "texas_holdem.core.evaluator",
        "texas_holdem.game.game_state",
        "texas_holdem.game.betting",
        "texas_holdem.game.game_engine",
        "texas_holdem.ui.cli",
        "texas_holdem.utils.constants"
    ]

    for module in modules:
        try:
            __import__(module)
            print(f"  OK {module}")
        except ImportError as e:
            print(f"  FAIL {module}: {e}")
            return False

    print("所有模块导入成功!\n")
    return True

def test_basic_functionality():
    """测试基本功能"""
    print("测试基本功能...")

    from texas_holdem.core.card import Card
    from texas_holdem.core.deck import Deck
    from texas_holdem.core.player import Player
    from texas_holdem.core.evaluator import PokerEvaluator

    # 测试Card
    card1 = Card('H', 'A')
    card2 = Card('S', 'K')
    assert card1 > card2, "A应该大于K"
    print("  OK Card比较")

    # 测试Deck
    deck = Deck()
    assert len(deck) == 52, "牌组应该有52张牌"
    deck.shuffle()
    card = deck.draw()
    assert len(deck) == 51, "抽牌后应该剩51张"
    print("  OK Deck功能")

    # 测试Player
    player = Player("测试", 1000)
    player.place_bet(100)
    assert player.chips == 900, "下注后筹码应该减少"
    assert player.bet_amount == 100, "下注额应该记录"
    print("  OK Player下注")

    # 测试手牌评估
    cards = [
        Card('H', 'A'), Card('H', 'K'), Card('H', 'Q'),
        Card('H', 'J'), Card('H', '10'), Card('C', '2'), Card('C', '3')
    ]
    rank, values = PokerEvaluator.evaluate_hand(cards)
    assert rank == PokerEvaluator.ROYAL_FLUSH, "应该是皇家同花顺"
    print("  OK 手牌评估")

    print("所有基本功能测试通过!\n")
    return True

def test_game_engine():
    """测试游戏引擎"""
    print("测试游戏引擎...")

    from texas_holdem.game.game_engine import GameEngine

    try:
        game = GameEngine(["玩家1", "玩家2"], initial_chips=500)
        print("  OK 游戏引擎初始化")

        # 测试开始新的一手牌
        game.start_new_hand()
        assert len(game.players[0].hand) == 2, "玩家1应该有2张底牌"
        assert len(game.players[1].hand) == 2, "玩家2应该有2张底牌"
        print("  OK 发底牌")

        # 测试盲注
        sb_player = [p for p in game.players if p.is_small_blind][0]
        bb_player = [p for p in game.players if p.is_big_blind][0]
        assert sb_player.bet_amount == 10, "小盲注应该是10"
        assert bb_player.bet_amount == 20, "大盲注应该是20"
        print("  OK 盲注系统")

        print("游戏引擎测试通过!\n")
        return True

    except Exception as e:
        print(f"  ✗ 游戏引擎测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("德州扑克游戏 - 最终功能验证")
    print("=" * 60)

    tests = [
        ("模块导入", test_imports),
        ("基本功能", test_basic_functionality),
        ("游戏引擎", test_game_engine)
    ]

    all_passed = True
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        try:
            if not test_func():
                all_passed = False
                print(f"FAIL {test_name} 失败")
        except Exception as e:
            print(f"FAIL {test_name} 异常: {e}")
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("SUCCESS 所有测试通过！游戏功能完整。")
        print("\n运行游戏:")
        print("  cd texas_holdem && python main.py")
        print("  或")
        print("  python demo.py")
    else:
        print("WARNING 部分测试失败，需要检查代码。")

    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)