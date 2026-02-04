"""
鲨鱼AI自动化测试 - 简化版
"""

import sys
import random
import io
from contextlib import redirect_stdout

sys.path.insert(0, 'd:\\workspace\\Texes')

from texas_holdem.ui.cli import CLI


class AutoCLI(CLI):
    """自动运行的CLI，无需用户输入"""
    
    def __init__(self):
        super().__init__()
        self.test_mode = True
        self.hand_count = 0
        self.max_hands = 100
        self.shark_stats = {
            'hands': 0,
            'wins': 0,
            'profit': 0,
            'eliminated': False
        }
    
    def get_player_action(self, player, betting_round):
        """自动获取行动，人类玩家也自动决策"""
        # 覆盖父类方法，让所有玩家都使用AI决策
        return self.get_ai_action(player, betting_round)
    
    def run_test_game(self, num_hands=100):
        """运行测试游戏"""
        self.max_hands = num_hands
        
        # 设置6个AI玩家
        self.player_names = ['电脑1号[鲨鱼]', '电脑2号[紧凶]', '电脑3号[松凶]', 
                            '电脑4号[紧弱]', '电脑5号[松弱]', '电脑6号[紧凶]']
        
        # 创建游戏引擎
        from texas_holdem.game.game_engine import GameEngine
        from texas_holdem.utils.constants import INITIAL_CHIPS
        
        self.game_engine = GameEngine(self.player_names, INITIAL_CHIPS)
        
        # 设置AI风格
        style_map = {'紧凶': 'TAG', '松凶': 'LAG', '紧弱': 'LAP', '松弱': 'LP', '鲨鱼': 'SHARK'}
        for player in self.game_engine.players:
            if '电脑' in player.name:
                player.is_ai = True
                if '[' in player.name and ']' in player.name:
                    cn_style = player.name.split('[')[1].split(']')[0]
                    player.ai_style = style_map.get(cn_style, 'LAG')
                self.player_styles[player.name] = player.ai_style
        
        # 初始化统计
        self._initialize_opponent_stats(self.game_engine.players)
        self.shark_ai.initialize_opponents(self.game_engine.players)
        self._initialize_player_stats()
        
        # 获取鲨鱼初始筹码
        shark = self._get_shark_player()
        shark_start_chips = shark.chips if shark else 0
        
        # 运行游戏
        f = io.StringIO()
        with redirect_stdout(f):  # 抑制输出
            try:
                self._run_auto_game_loop()
            except Exception as e:
                print(f"[测试中断: {e}]")
        
        # 计算结果
        shark = self._get_shark_player()
        shark_end_chips = shark.chips if shark else 0
        
        self.shark_stats['profit'] = shark_end_chips - shark_start_chips
        self.shark_stats['eliminated'] = (shark is None or shark.chips <= 0)
        
        return self.shark_stats
    
    def _get_shark_player(self):
        """获取鲨鱼玩家"""
        for player in self.game_engine.players:
            if getattr(player, 'ai_style', '') == 'SHARK':
                return player
        return None
    
    def _run_auto_game_loop(self):
        """自动游戏循环"""
        hand_number = 0
        
        while hand_number < self.max_hands:
            hand_number += 1
            self.total_hands += 1
            self.hand_count = hand_number
            
            # 检查鲨鱼是否还在
            shark = self._get_shark_player()
            if not shark or shark.chips <= 0:
                self.shark_stats['eliminated'] = True
                break
            
            # 开始新一手
            self.game_engine.start_new_hand()
            self.shark_stats['hands'] += 1
            
            # 更新统计数据
            for player in self.game_engine.players:
                if player.name in self.player_stats:
                    self.player_stats[player.name]['hands_played'] += 1
            
            # 运行各个街
            if not self._run_betting_round_auto():
                continue
            
            if len([p for p in self.game_engine.players if p.is_active]) > 1:
                self.game_engine.deal_flop()
                self._update_shark_after_deal()
                if not self._run_betting_round_auto():
                    continue
            
            if len([p for p in self.game_engine.players if p.is_active]) > 1:
                self.game_engine.deal_turn()
                if not self._run_betting_round_auto():
                    continue
            
            if len([p for p in self.game_engine.players if p.is_active]) > 1:
                self.game_engine.deal_river()
                if not self._run_betting_round_auto():
                    continue
            
            # 结算
            self._resolve_showdown_auto()
    
    def _run_betting_round_auto(self):
        """自动运行下注轮"""
        from texas_holdem.game.betting import BettingRound
        
        betting_round = BettingRound(self.game_engine.game_state)
        self.current_betting_round = betting_round
        
        max_actions = 50
        action_count = 0
        
        while not betting_round.is_complete() and action_count < max_actions:
            current_player = betting_round.get_current_player()
            if not current_player or not current_player.is_active:
                betting_round.next_player()
                continue
            
            # 获取行动
            action, amount = self.get_ai_action(current_player, betting_round)
            if action is None:
                betting_round.next_player()
                continue
            
            # 更新鲨鱼追踪
            if getattr(current_player, 'ai_style', '') != 'SHARK':
                action_str = action.name.lower() if hasattr(action, 'name') else str(action).lower()
                street = str(self.game_engine.game_state.state).lower()
                self.shark_ai.update_after_action(current_player.name, action_str, street)
            
            # 执行行动
            success, msg, bet_amount = betting_round.process_action(current_player, action, amount)
            if success:
                self._update_player_stats(current_player, action, bet_amount)
            
            action_count += 1
            
            # 检查是否只剩一个玩家
            active_players = [p for p in self.game_engine.players if p.is_active]
            if len(active_players) <= 1:
                return False
        
        # 收集下注
        betting_round.collect_bets()
        self.game_engine.game_state.advance_stage()
        return True
    
    def _update_shark_after_deal(self):
        """发牌后更新（供子类扩展）"""
        pass
    
    def _resolve_showdown_auto(self):
        """自动结算摊牌"""
        from texas_holdem.core.evaluator import PokerEvaluator
        
        game_state = self.game_engine.game_state
        active_players = [p for p in game_state.players if p.is_active]
        
        if len(active_players) == 0:
            return
        
        if len(active_players) == 1:
            winner = active_players[0]
            winner.chips += game_state.table.total_pot
            if getattr(winner, 'ai_style', '') == 'SHARK':
                self.shark_stats['wins'] += 1
            return
        
        # 摊牌比大小
        community_cards = game_state.table.community_cards
        if len(community_cards) < 5:
            return
        
        best_rank = float('inf')
        winners = []
        
        for player in active_players:
            if player.hand and len(player.hand.cards) == 2:
                all_cards = player.hand.cards + community_cards
                try:
                    rank, values = PokerEvaluator.evaluate_hand(all_cards)
                    if rank < best_rank:
                        best_rank = rank
                        winners = [player]
                    elif rank == best_rank:
                        winners.append(player)
                except:
                    continue
        
        if winners:
            win_amount = game_state.table.total_pot // len(winners)
            for winner in winners:
                winner.chips += win_amount
                if getattr(winner, 'ai_style', '') == 'SHARK':
                    self.shark_stats['wins'] += 1


def run_tests(num_tests=3, num_hands=100):
    """运行多次测试"""
    print(f"\n{'#'*60}")
    print(f"#  Shark AI Auto Test - {num_tests} rounds x {num_hands} hands")
    print(f"{'#'*60}\n")
    
    all_stats = []
    
    for i in range(1, num_tests + 1):
        print(f"Running test {i}/{num_tests}...")
        
        auto_cli = AutoCLI()
        stats = auto_cli.run_test_game(num_hands)
        all_stats.append(stats)
        
        print(f"  Hands: {stats['hands']}, Wins: {stats['wins']}, Profit: {stats['profit']:+d}, Eliminated: {stats['eliminated']}")
    
    # 汇总
    print(f"\n{'='*60}")
    print("Summary:")
    
    total_profit = sum(s['profit'] for s in all_stats)
    total_wins = sum(s['wins'] for s in all_stats)
    total_hands = sum(s['hands'] for s in all_stats)
    eliminations = sum(1 for s in all_stats if s['eliminated'])
    
    print(f"  Total profit: {total_profit}")
    print(f"  Total wins: {total_wins}/{total_hands}")
    print(f"  Eliminations: {eliminations}/{num_tests}")
    print(f"  Avg profit: {total_profit/num_tests:+.0f}")
    
    # 判断是否通过
    wins_count = sum(1 for s in all_stats if s['profit'] > 0)
    if wins_count >= num_tests * 0.7 and eliminations == 0:
        print("\n  [PASS] Shark AI is stable!")
    elif wins_count >= num_tests * 0.5:
        print("\n  [WARN] Needs improvement")
    else:
        print("\n  [FAIL] Needs significant improvement")
    
    print(f"{'='*60}\n")
    
    return all_stats


if __name__ == '__main__':
    run_tests(3, 100)
