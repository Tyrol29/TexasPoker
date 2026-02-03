"""
游戏常量定义
"""

# 游戏配置
INITIAL_CHIPS = 4000  # 初始筹码 (200个大盲)
SMALL_BLIND = 10      # 小盲注
BIG_BLIND = 20        # 大盲注

# 游戏状态
class GameState:
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"
    SHOWDOWN = "showdown"
    GAME_OVER = "game_over"

# 玩家行动
class Action:
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    BET = "bet"
    RAISE = "raise"
    ALL_IN = "all_in"

# 下注轮次
class BettingRound:
    PRE_FLOP = "pre_flop"
    FLOP = "flop"
    TURN = "turn"
    RIVER = "river"

# 手牌评估结果
HAND_RANK_NAMES = {
    0: "High Card",
    1: "One Pair",
    2: "Two Pair",
    3: "Three of a Kind",
    4: "Straight",
    5: "Flush",
    6: "Full House",
    7: "Four of a Kind",
    8: "Straight Flush",
    9: "Royal Flush"
}