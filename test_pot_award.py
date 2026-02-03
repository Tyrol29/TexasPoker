"""
测试筹码分配修复
验证当玩家获胜时，筹码正确增加
"""

from texas_holdem.game.game_engine import GameEngine
from texas_holdem.core.player import Player
from texas_holdem.core.table import Table

def test_single_winner_pot_collection():
    """测试：只剩一个玩家时，底池正确分配"""
    print("=" * 50)
    print("测试1: 单赢家底池收集")
    print("=" * 50)
    
    engine = GameEngine(['玩家1', '玩家2'], 1000)
    engine.start_new_hand()
    
    # 记录初始筹码
    initial_chips = {p.name: p.chips for p in engine.players}
    print(f"初始筹码: {initial_chips}")
    
    # 模拟下注（翻牌前）
    # 玩家已下盲注：玩家1(SB)=10, 玩家2(BB)=20
    engine.players[0].place_bet(30)  # 再加30
    engine.players[1].place_bet(20)  # 跟注
    
    # 当前状态
    print(f"\n下注后:")
    for p in engine.players:
        print(f"  {p.name}: {p.chips} 筹码, 已下注: {p.bet_amount}")
    
    # 模拟玩家2弃牌（只剩一个玩家）
    engine.players[1].fold()
    engine.game_state.update_active_players()
    
    print(f"\n玩家2弃牌后:")
    print(f"  活动玩家数: {engine.game_state.get_active_player_count()}")
    print(f"  底池(收集前): {engine.game_state.table.total_pot}")
    
    # 模拟 run_betting_round 的行为：收集下注再返回
    engine.betting_round.collect_bets()
    print(f"  底池(收集后): {engine.game_state.table.total_pot}")
    
    # 分配底池
    winner = engine.game_state.get_active_players()[0]
    win_amount = engine.game_state.table.total_pot
    winner.collect_winnings(win_amount)
    
    print(f"\n赢家: {winner.name}, 赢得: {win_amount}")
    
    # 验证筹码
    print(f"\n最终筹码:")
    for p in engine.players:
        print(f"  {p.name}: {p.chips}")
    
    # 验证总筹码守恒
    total_chips = sum(p.chips for p in engine.players)
    expected_total = 2000  # 2 * 1000
    print(f"\n总筹码: {total_chips}, 预期: {expected_total}")
    
    if total_chips == expected_total:
        print("[PASS] 测试通过：筹码守恒")
    else:
        print("[FAIL] 测试失败：筹码不守恒！")
        return False
    
    # 验证赢家筹码增加
    if winner.chips > initial_chips[winner.name]:
        print(f"[PASS] 赢家 {winner.name} 筹码增加: {initial_chips[winner.name]} -> {winner.chips}")
    else:
        print(f"[FAIL] 赢家筹码未增加！")
        return False
    
    return True


def test_multiple_betting_rounds():
    """测试：多轮下注后只剩一个玩家"""
    print("\n" + "=" * 50)
    print("测试2: 多轮下注后弃牌")
    print("=" * 50)
    
    engine = GameEngine(['玩家1', '玩家2'], 1000)
    engine.start_new_hand()
    
    initial_chips = {p.name: p.chips for p in engine.players}
    print(f"初始筹码: {initial_chips}")
    
    # 翻牌前下注
    engine.players[0].place_bet(30)   # 再加30 (总40)
    engine.players[1].place_bet(20)   # 跟注 (总40)
    
    # 收集翻牌前下注
    engine.betting_round.collect_bets()
    collected_pot = engine.game_state.table.total_pot
    print(f"翻牌前底池: {collected_pot}")
    
    # 发翻牌
    engine.deal_flop()
    engine.game_state.advance_stage()
    
    # 翻牌圈下注
    engine.players[0].place_bet(50)
    engine.players[1].place_bet(50)
    
    print(f"翻牌圈下注后:")
    for p in engine.players:
        print(f"  {p.name}: {p.chips} 筹码, 已下注: {p.bet_amount}")
    
    # 玩家2弃牌
    engine.players[1].fold()
    engine.game_state.update_active_players()
    
    # 这是关键：在只剩一个玩家时，必须先收集再分配
    print(f"\n底池(收集前): {engine.game_state.table.total_pot}")
    engine.betting_round.collect_bets()
    print(f"底池(收集后): {engine.game_state.table.total_pot}")
    
    winner = engine.game_state.get_active_players()[0]
    win_amount = engine.game_state.table.total_pot
    winner.collect_winnings(win_amount)
    
    print(f"\n赢家: {winner.name}, 赢得: {win_amount}")
    
    # 验证
    total_chips = sum(p.chips for p in engine.players)
    print(f"总筹码: {total_chips}, 预期: 2000")
    
    if total_chips == 2000 and win_amount > collected_pot:
        print("[PASS] 测试通过：翻牌圈下注被正确收集")
        return True
    else:
        print("[FAIL] 测试失败！")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("筹码分配修复测试")
    print("=" * 50 + "\n")
    
    results = []
    
    try:
        results.append(("单赢家底池收集", test_single_winner_pot_collection()))
    except Exception as e:
        print(f"测试1异常: {e}")
        import traceback
        traceback.print_exc()
        results.append(("单赢家底池收集", False))
    
    try:
        results.append(("多轮下注后弃牌", test_multiple_betting_rounds()))
    except Exception as e:
        print(f"测试2异常: {e}")
        import traceback
        traceback.print_exc()
        results.append(("多轮下注后弃牌", False))
    
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{name}: {status}")
    
    all_passed = all(passed for _, passed in results)
    print("\n" + ("所有测试通过！" if all_passed else "有测试失败！"))
