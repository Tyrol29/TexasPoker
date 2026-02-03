"""
游戏状态管理类
管理游戏的整体状态和玩家轮转
"""

from typing import List, Optional
from ..core.player import Player
from ..core.table import Table
from ..utils.constants import GameState

class GameStateManager:
    def __init__(self, players: List[Player]):
        """
        初始化游戏状态管理器

        Args:
            players: 玩家列表
        """
        self.players = players
        self.table = Table()
        self.state = GameState.PRE_FLOP
        self.current_player_index = 0
        self.current_bet = 0  # 当前轮次需要跟注的金额
        self.last_raiser_index = -1  # 最后加注的玩家索引
        self.min_raise = 0  # 最小加注金额
        self.hand_number = 0  # 当前手牌编号
        self.active_players = [p for p in players if p.is_active]
        self.winners = []

    def reset_for_new_hand(self):
        """为新的一手牌重置状态"""
        self.state = GameState.PRE_FLOP
        self.current_bet = 0
        self.last_raiser_index = -1
        self.min_raise = 0
        self.winners.clear()
        self.table.reset()

        # 重置所有玩家状态
        for player in self.players:
            player.reset_for_new_hand()

        # 设置盲注位置
        if len(self.players) >= 2:
            # 简单轮转：庄家位置轮转
            dealer_index = self.hand_number % len(self.players)
            small_blind_index = (dealer_index + 1) % len(self.players)
            big_blind_index = (dealer_index + 2) % len(self.players)

            self.players[dealer_index].is_dealer = True
            self.players[small_blind_index].is_small_blind = True
            self.players[big_blind_index].is_big_blind = True

            # 当前玩家从大盲注后的玩家开始
            self.current_player_index = (big_blind_index + 1) % len(self.players)

        # 更新活动玩家列表
        self.active_players = [p for p in self.players if p.is_active]

        self.hand_number += 1

    def next_player(self):
        """移动到下一个活动玩家"""
        if not self.active_players:
            return None

        start_index = self.current_player_index
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            player = self.players[self.current_player_index]

            if player.is_active and not player.is_all_in:
                return player

            # 如果回到起点，说明没有更多可行动的玩家
            if self.current_player_index == start_index:
                return None

    def get_current_player(self) -> Optional[Player]:
        """获取当前玩家"""
        if not self.active_players:
            return None

        player = self.players[self.current_player_index]
        if player.is_active and not player.is_all_in:
            return player

        # 如果当前玩家不能行动，找到下一个可行动的玩家
        return self.next_player()

    def update_active_players(self):
        """更新活动玩家列表"""
        self.active_players = [p for p in self.players if p.is_active]

    def get_active_players(self) -> List[Player]:
        """获取所有活动玩家"""
        return self.active_players.copy()

    def get_active_player_count(self) -> int:
        """获取活动玩家数量"""
        return len(self.active_players)

    def get_folded_players(self) -> List[Player]:
        """获取已弃牌的玩家"""
        return [p for p in self.players if not p.is_active]

    def get_all_in_players(self) -> List[Player]:
        """获取全押玩家"""
        return [p for p in self.players if p.is_all_in]

    def is_betting_round_complete(self) -> bool:
        """
        检查当前下注轮次是否完成

        Returns:
            如果下注轮次完成返回True
        """
        if len(self.active_players) <= 1:
            return True

        # 检查是否所有玩家都已行动或全押
        for player in self.active_players:
            if not player.has_acted and not player.is_all_in:
                return False

        # 检查是否所有玩家下注额相等或全押
        active_bets = [p.bet_amount for p in self.active_players if not p.is_all_in]
        if active_bets:
            first_bet = active_bets[0]
            for bet in active_bets[1:]:
                if bet != first_bet:
                    return False

        return True

    def reset_player_actions(self):
        """重置所有玩家的行动状态"""
        for player in self.players:
            player.has_acted = False

    def advance_stage(self):
        """推进到下一个游戏阶段"""
        if self.state == GameState.PRE_FLOP:
            self.state = GameState.FLOP
        elif self.state == GameState.FLOP:
            self.state = GameState.TURN
        elif self.state == GameState.TURN:
            self.state = GameState.RIVER
        elif self.state == GameState.RIVER:
            self.state = GameState.SHOWDOWN
        else:
            self.state = GameState.GAME_OVER

        # 重置下注状态
        self.current_bet = 0
        self.last_raiser_index = -1
        self.min_raise = 0
        self.reset_player_actions()

        # 更新当前玩家为第一个活动玩家
        if self.active_players:
            self.current_player_index = self.players.index(self.active_players[0])

    def set_winners(self, winners: List[Player]):
        """设置赢家"""
        self.winners = winners

    def get_winners(self) -> List[Player]:
        """获取赢家"""
        return self.winners.copy()

    def __str__(self):
        state_names = {
            GameState.PRE_FLOP: "翻牌前",
            GameState.FLOP: "翻牌圈",
            GameState.TURN: "转牌圈",
            GameState.RIVER: "河牌圈",
            GameState.SHOWDOWN: "摊牌",
            GameState.GAME_OVER: "游戏结束"
        }

        return (f"手牌 #{self.hand_number} | "
                f"阶段: {state_names.get(self.state, self.state)} | "
                f"活动玩家: {len(self.active_players)} | "
                f"当前下注: {self.current_bet} | "
                f"最小加注: {self.min_raise}")