"""
游戏引擎主循环
控制德州扑克的完整游戏流程
"""

import time
from typing import List, Dict, Optional
from ..core.deck import Deck
from ..core.player import Player
from ..core.table import Table
from ..core.evaluator import PokerEvaluator
from .game_state import GameStateManager
from .betting import BettingRound
from ..utils.constants import GameState, SMALL_BLIND, BIG_BLIND

class GameEngine:
    def __init__(self, player_names: List[str], initial_chips: int = 1000):
        """
        初始化游戏引擎

        Args:
            player_names: 玩家名称列表
            initial_chips: 初始筹码数量
        """
        if len(player_names) < 2 or len(player_names) > 8:
            raise ValueError("目前支持2-8人游戏")

        self.players = [Player(name, initial_chips) for name in player_names]
        self.game_state = GameStateManager(self.players)
        self.deck = Deck()
        self.betting_round = BettingRound(self.game_state)
        self.is_running = False

    def start_new_hand(self):
        """开始新的一手牌"""
        # 重置游戏状态
        self.game_state.reset_for_new_hand()
        self.deck.reset()
        self.deck.shuffle()

        # 发底牌
        for player in self.players:
            player.hand.add_cards(self.deck.draw(2))

        # 发布小盲注和大盲注（筹码不足时自动全押）
        for player in self.players:
            if player.is_small_blind:
                if player.chips <= SMALL_BLIND:
                    player.all_in()
                else:
                    player.place_bet(SMALL_BLIND)
            elif player.is_big_blind:
                if player.chips <= BIG_BLIND:
                    player.all_in()
                else:
                    player.place_bet(BIG_BLIND)

        # 设置初始下注状态
        self.game_state.current_bet = BIG_BLIND
        self.game_state.min_raise = BIG_BLIND - SMALL_BLIND  # 最小加注为大盲注减去小盲注

        print(f"\n=== 开始第 {self.game_state.hand_number} 手牌 ===")
        print(f"庄家: {[p.name for p in self.players if p.is_dealer][0]}")
        print(f"小盲注: {SMALL_BLIND}, 大盲注: {BIG_BLIND}")

    def deal_flop(self):
        """发翻牌（3张公共牌）"""
        # 烧一张牌
        self.deck.draw(1)
        # 发3张翻牌
        flop_cards = self.deck.draw(3)
        self.game_state.table.add_community_cards(flop_cards)
        print(f"\n翻牌: {' '.join(str(card) for card in flop_cards)}")

    def deal_turn(self):
        """发转牌（第4张公共牌）"""
        # 烧一张牌
        self.deck.draw(1)
        # 发转牌
        turn_card = self.deck.draw(1)
        self.game_state.table.add_community_card(turn_card)
        print(f"\n转牌: {turn_card}")

    def deal_river(self):
        """发河牌（第5张公共牌）"""
        # 烧一张牌
        self.deck.draw(1)
        # 发河牌
        river_card = self.deck.draw(1)
        self.game_state.table.add_community_card(river_card)
        print(f"\n河牌: {river_card}")

    def run_betting_round(self) -> bool:
        """
        运行一个下注轮次

        Returns:
            如果游戏继续返回True，如果只剩一个玩家返回False
        """
        round_name = {
            GameState.PRE_FLOP: "翻牌前",
            GameState.FLOP: "翻牌圈",
            GameState.TURN: "转牌圈",
            GameState.RIVER: "河牌圈"
        }.get(self.game_state.state, "下注")

        print(f"\n--- {round_name}下注开始 ---")

        # 重置玩家行动状态
        self.game_state.reset_player_actions()

        # 下注轮次循环
        while not self.game_state.is_betting_round_complete():
            current_player = self.game_state.get_current_player()
            if not current_player:
                break

            print(f"\n{current_player.name} 的回合")
            print(f"手牌: {current_player.hand}")
            print(f"筹码: {current_player.chips}")
            print(f"当前下注额: {self.game_state.current_bet}")
            print(f"需要跟注: {self.betting_round.get_amount_to_call(current_player)}")

            # 获取可用行动
            available_actions = self.betting_round.get_available_actions(current_player)
            print(f"可用行动: {', '.join(available_actions)}")

            # 获取玩家行动（这里由UI处理，我们只是模拟）
            # 在实际游戏中，这里会调用UI获取玩家输入
            # 现在我们先模拟一个简单的AI行动
            action, amount = self._get_simulated_action(current_player, available_actions)

            # 处理行动
            success, message, bet_amount = self.betting_round.process_action(
                current_player, action, amount
            )

            if success:
                print(f"> {message}")
                if bet_amount > 0:
                    print(f"  下注后筹码: {current_player.chips}")
            else:
                print(f"> 行动失败: {message}")

            # 移动到下一个玩家
            self.game_state.next_player()

            # 检查是否只剩一个活动玩家
            if self.game_state.get_active_player_count() <= 1:
                print("\n只剩一个活动玩家，下注轮次结束")
                # 先收集下注到底池
                side_pots = self.betting_round.collect_bets()
                if side_pots:
                    print(f"创建了 {len(side_pots)} 个边池")
                return False

        print(f"\n--- {round_name}下注结束 ---")

        # 收集下注到底池
        side_pots = self.betting_round.collect_bets()
        if side_pots:
            print(f"创建了 {len(side_pots)} 个边池")

        print(f"总底池: {self.game_state.table.total_pot}")
        return True

    def _get_simulated_action(self, player: Player, available_actions: List[str]) -> tuple:
        """
        模拟玩家行动（简单AI）

        Args:
            player: 玩家
            available_actions: 可用行动列表

        Returns:
            (行动, 金额) 元组
        """
        import random

        # 简单AI逻辑
        amount_to_call = self.betting_round.get_amount_to_call(player)

        # 如果有加注选项，有时会加注
        if "raise" in available_actions and random.random() < 0.3:
            min_raise = max(self.game_state.min_raise, 1)  # 确保最小加注至少为1
            max_raise = min(player.chips - amount_to_call, min_raise * 3)
            if max_raise >= min_raise:  # 确保有效范围
                raise_amount = random.randint(min_raise, max_raise)
                return "raise", raise_amount

        # 如果有下注选项，有时会下注
        elif "bet" in available_actions and random.random() < 0.4:
            # 设置最小下注（如果没有当前下注，使用大盲注作为基准）
            min_bet = max(self.game_state.min_raise, 10)  # 至少10
            max_bet = min(player.chips, min_bet * 2)
            if max_bet >= min_bet:  # 确保有效范围
                bet_amount = random.randint(min_bet, max_bet)
                return "bet", bet_amount

        # 如果可以过牌且没有好牌，过牌
        elif "check" in available_actions and random.random() < 0.7:
            return "check", 0

        # 如果可以跟注，通常跟注
        elif "call" in available_actions:
            return "call", 0

        # 如果有弃牌选项，很少弃牌
        elif "fold" in available_actions and random.random() < 0.1:
            return "fold", 0

        # 默认全押
        return "all_in", 0

    def determine_showdown_winners(self) -> List[Player]:
        """
        确定摊牌赢家

        Returns:
            赢家列表
        """
        active_players = self.game_state.get_active_players()
        community_cards = self.game_state.table.get_community_cards()

        if len(active_players) == 1:
            # 只剩一个玩家，自动获胜
            return active_players

        # 比较所有活动玩家的手牌
        player_hands = {}
        for player in active_players:
            all_cards = player.hand.get_cards() + community_cards
            player_hands[player] = all_cards

        # 找到最佳手牌
        best_players = []
        best_result = None

        for player, cards in player_hands.items():
            rank, values = PokerEvaluator.evaluate_hand(cards)

            if best_result is None:
                best_result = (rank, values)
                best_players = [player]
            else:
                comparison = PokerEvaluator.compare_hands(cards, player_hands[best_players[0]])
                if comparison == 1:  # 当前玩家更强
                    best_result = (rank, values)
                    best_players = [player]
                elif comparison == 0:  # 平局
                    best_players.append(player)

        return best_players

    def award_pots(self, winners: List[Player]):
        """分配底池给赢家"""
        if not winners:
            return

        # 确定每个底池的赢家
        winners_by_pot = {}

        # 主池赢家
        main_pot_winners = []
        for winner in winners:
            if winner in self.game_state.table.main_pot.eligible_players:
                main_pot_winners.append(winner)
        if main_pot_winners:
            winners_by_pot[self.game_state.table.main_pot] = main_pot_winners

        # 边池赢家
        for side_pot in self.game_state.table.side_pots:
            side_pot_winners = []
            for winner in winners:
                if winner in side_pot.eligible_players:
                    side_pot_winners.append(winner)
            if side_pot_winners:
                winners_by_pot[side_pot] = side_pot_winners

        # 分配筹码
        winnings = self.game_state.table.award_pots(winners_by_pot)

        # 显示赢家信息
        print("\n=== 摊牌结果 ===")
        community_cards = self.game_state.table.get_community_cards()
        print(f"公共牌: {' '.join(str(card) for card in community_cards)}")

        for player in self.game_state.get_active_players():
            all_cards = player.hand.get_cards() + community_cards
            hand_desc = PokerEvaluator.get_best_hand_description(all_cards)
            print(f"{player.name}: {player.hand} - {hand_desc}")

        print(f"\n赢家: {', '.join(w.name for w in winners)}")

        for player, amount in winnings.items():
            player.collect_winnings(amount)
            print(f"{player.name} 赢得 {amount} 筹码")
        
        return winnings

    def run_hand(self):
        """运行一手完整的牌"""
        # 开始新的一手牌
        self.start_new_hand()

        # 翻牌前下注
        if not self.run_betting_round():
            # 只剩一个玩家，游戏结束
            winner = self.game_state.get_active_players()[0]
            print(f"\n所有其他玩家弃牌，{winner.name} 获胜!")
            winner.collect_winnings(self.game_state.table.total_pot)
            return

        # 发翻牌
        self.deal_flop()
        self.game_state.advance_stage()

        # 翻牌圈下注
        if not self.run_betting_round():
            winner = self.game_state.get_active_players()[0]
            print(f"\n所有其他玩家弃牌，{winner.name} 获胜!")
            winner.collect_winnings(self.game_state.table.total_pot)
            return

        # 发转牌
        self.deal_turn()
        self.game_state.advance_stage()

        # 转牌圈下注
        if not self.run_betting_round():
            winner = self.game_state.get_active_players()[0]
            print(f"\n所有其他玩家弃牌，{winner.name} 获胜!")
            winner.collect_winnings(self.game_state.table.total_pot)
            return

        # 发河牌
        self.deal_river()
        self.game_state.advance_stage()

        # 河牌圈下注
        if not self.run_betting_round():
            winner = self.game_state.get_active_players()[0]
            print(f"\n所有其他玩家弃牌，{winner.name} 获胜!")
            winner.collect_winnings(self.game_state.table.total_pot)
            return

        # 摊牌
        self.game_state.advance_stage()
        winners = self.determine_showdown_winners()
        self.award_pots(winners)

    def run(self, max_hands: int = 10):
        """
        运行游戏主循环

        Args:
            max_hands: 最大手牌数
        """
        self.is_running = True
        hand_count = 0

        print("=== 德州扑克游戏开始 ===")
        print(f"玩家: {', '.join(p.name for p in self.players)}")

        while self.is_running and hand_count < max_hands:
            # 检查是否有玩家出局
            active_players = [p for p in self.players if p.chips > 0]
            if len(active_players) < 2:
                print(f"\n游戏结束! 只剩 {len(active_players)} 个玩家有筹码")
                break

            hand_count += 1
            self.run_hand()

            # 显示玩家筹码状态
            print("\n玩家筹码状态:")
            for player in self.players:
                print(f"  {player}")

            # 询问是否继续
            if hand_count < max_hands:
                # 在实际游戏中，这里会询问用户
                # 现在我们先自动继续
                print("\n准备下一手牌...")
                time.sleep(1)

        print("\n=== 游戏结束 ===")
        print("最终筹码状态:")
        for player in self.players:
            print(f"  {player}")

        self.is_running = False
    def remove_eliminated_players(self) -> List[Player]:
        """
        移除筹码归零的玩家（淘汰机制）
        
        Returns:
            被淘汰的玩家列表
        """
        eliminated = []
        remaining = []
        
        for player in self.players:
            if player.chips <= 0:
                eliminated.append(player)
            else:
                remaining.append(player)
        
        if eliminated:
            self.players = remaining
            # 更新游戏状态中的玩家列表
            self.game_state.players = remaining
            self.game_state.active_players = [p for p in remaining if p.is_active]
            
        return eliminated
    
    def get_remaining_players(self) -> List[Player]:
        """获取剩余有筹码的玩家"""
        return [p for p in self.players if p.chips > 0]
    
    def get_human_players(self) -> List[Player]:
        """获取人类玩家列表"""
        return [p for p in self.players if not p.is_ai]
    
    def get_ai_players(self) -> List[Player]:
        """获取AI玩家列表"""
        return [p for p in self.players if p.is_ai]
