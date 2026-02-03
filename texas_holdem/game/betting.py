"""
下注逻辑系统
管理德州扑克的下注轮次和行动验证
"""

from typing import List, Tuple, Optional
from ..core.player import Player
from .game_state import GameStateManager
from ..utils.constants import Action

class BettingRound:
    def __init__(self, game_state: GameStateManager):
        """
        初始化下注轮次

        Args:
            game_state: 游戏状态管理器
        """
        self.game_state = game_state
        self.players = game_state.players

    def validate_action(self, player: Player, action: str, amount: int = 0) -> Tuple[bool, str]:
        """
        验证玩家行动是否有效

        Args:
            player: 执行行动的玩家
            action: 行动类型
            amount: 下注/加注金额

        Returns:
            (是否有效, 错误信息)
        """
        if not player.is_active:
            return False, "玩家已弃牌"

        if player.is_all_in:
            return False, "玩家已全押"

        current_bet = self.game_state.current_bet
        amount_to_call = player.get_amount_to_call(current_bet)

        if action == Action.FOLD:
            return True, ""

        elif action == Action.CHECK:
            if amount_to_call > 0:
                return False, "需要跟注，不能过牌"
            return True, ""

        elif action == Action.CALL:
            if amount_to_call <= 0:
                return False, "无需跟注，可以过牌"
            if amount_to_call > player.chips:
                return True, ""  # 可以全押
            return True, ""

        elif action == Action.BET:
            if current_bet > 0:
                return False, "已有下注，请使用加注"
            if amount <= 0:
                return False, "下注金额必须大于0"
            if amount < self.game_state.min_raise:
                return False, f"最小下注额为{self.game_state.min_raise}"
            if amount > player.chips:
                return True, ""  # 可以全押
            return True, ""

        elif action == Action.RAISE:
            if current_bet == 0:
                return False, "没有下注可以加注，请使用下注"
            if amount <= 0:
                return False, "加注金额必须大于0"

            total_amount = amount_to_call + amount
            min_raise = self.game_state.min_raise

            if amount < min_raise:
                return False, f"最小加注额为{min_raise}"

            if total_amount > player.chips:
                return True, ""  # 可以全押

            return True, ""

        elif action == Action.ALL_IN:
            if player.chips == 0:
                return False, "没有筹码可以全押"
            return True, ""

        return False, f"未知行动: {action}"

    def process_action(self, player: Player, action: str, amount: int = 0) -> Tuple[bool, str, int]:
        """
        处理玩家行动

        Args:
            player: 执行行动的玩家
            action: 行动类型
            amount: 下注/加注金额

        Returns:
            (是否成功, 消息, 实际下注金额)
        """
        is_valid, error_msg = self.validate_action(player, action, amount)
        if not is_valid:
            return False, error_msg, 0

        current_bet = self.game_state.current_bet
        amount_to_call = player.get_amount_to_call(current_bet)
        actual_amount = 0

        if action == Action.FOLD:
            player.fold()
            self.game_state.update_active_players()
            return True, f"{player.name} 弃牌", 0

        elif action == Action.CHECK:
            player.check()
            return True, f"{player.name} 过牌", 0

        elif action == Action.CALL:
            if amount_to_call >= player.chips:
                # 不够跟注，全押
                actual_amount = player.all_in()
                return True, f"{player.name} 全押 {actual_amount}", actual_amount
            else:
                actual_amount = player.call(current_bet)
                return True, f"{player.name} 跟注 {actual_amount}", actual_amount

        elif action == Action.BET:
            if amount >= player.chips:
                # 下注金额超过筹码，全押
                actual_amount = player.all_in()
                return True, f"{player.name} 全押 {actual_amount}", actual_amount
            else:
                actual_amount = player.place_bet(amount)
                self.game_state.current_bet = amount
                self.game_state.last_raiser_index = self.players.index(player)
                self.game_state.min_raise = amount  # 下注后，最小加注等于下注金额
                return True, f"{player.name} 下注 {actual_amount}", actual_amount

        elif action == Action.RAISE:
            total_amount = amount_to_call + amount

            if total_amount >= player.chips:
                # 加注金额超过筹码，全押
                actual_amount = player.all_in()
                # 更新当前下注额
                player_bet = player.bet_amount
                if player_bet > self.game_state.current_bet:
                    self.game_state.current_bet = player_bet
                    self.game_state.last_raiser_index = self.players.index(player)
                    # 计算最小加注
                    self.game_state.min_raise = player_bet - current_bet
                return True, f"{player.name} 全押 {actual_amount}", actual_amount
            else:
                actual_amount = player.raise_bet(current_bet, amount)
                self.game_state.current_bet = current_bet + amount
                self.game_state.last_raiser_index = self.players.index(player)
                self.game_state.min_raise = amount
                return True, f"{player.name} 加注到 {self.game_state.current_bet}", actual_amount

        elif action == Action.ALL_IN:
            actual_amount = player.all_in()
            # 更新当前下注额如果全押金额更大
            if player.bet_amount > self.game_state.current_bet:
                self.game_state.current_bet = player.bet_amount
                self.game_state.last_raiser_index = self.players.index(player)
                # 计算最小加注
                self.game_state.min_raise = player.bet_amount - current_bet
            return True, f"{player.name} 全押 {actual_amount}", actual_amount

        return False, f"处理行动失败: {action}", 0

    def collect_bets(self) -> List:
        """收集所有玩家的下注到底池"""
        return self.game_state.table.collect_bets(self.players)

    def get_available_actions(self, player: Player) -> List[str]:
        """
        获取玩家可用的行动

        Args:
            player: 玩家

        Returns:
            可用行动列表
        """
        if not player.is_active or player.is_all_in:
            return []

        actions = []
        current_bet = self.game_state.current_bet
        amount_to_call = player.get_amount_to_call(current_bet)

        # 总是可以弃牌
        actions.append(Action.FOLD)

        if amount_to_call <= 0:
            # 可以过牌
            actions.append(Action.CHECK)
            # 如果没有当前下注，可以下注；否则只能加注
            if current_bet == 0 and player.chips > 0:
                actions.append(Action.BET)
            elif current_bet > 0 and player.chips > 0:
                actions.append(Action.RAISE)
        else:
            # 可以跟注或加注
            if player.chips >= amount_to_call:
                actions.append(Action.CALL)
            else:
                # 筹码不够跟注，只能全押
                actions.append(Action.ALL_IN)
                return actions

            # 检查是否可以加注
            if player.chips > amount_to_call:
                actions.append(Action.RAISE)

        # 总是可以全押
        if player.chips > 0:
            actions.append(Action.ALL_IN)

        return actions

    def get_min_bet(self) -> int:
        """获取最小下注额"""
        return self.game_state.min_raise

    def get_amount_to_call(self, player: Player) -> int:
        """获取玩家需要跟注的金额"""
        current_bet = self.game_state.current_bet
        amount_to_call = player.get_amount_to_call(current_bet)
        return max(0, amount_to_call)