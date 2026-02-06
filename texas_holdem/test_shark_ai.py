"""
鲨鱼AI自动化测试脚本 - 输牌分析版
6个电脑自动对局，详细记录鲨鱼AI输牌时的技术数据
用于策略改进分析
"""

import sys
import random
from typing import List, Dict, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field

# 添加项目路径
sys.path.insert(0, r'd:\workspace\Texes')

from texas_holdem.core.card import Card
from texas_holdem.core.deck import Deck
from texas_holdem.core.player import Player
from texas_holdem.core.table import Table
from texas_holdem.game.game_state import GameState
from texas_holdem.game.game_engine import GameEngine
from texas_holdem.ai.ai_engine import AIEngine
from texas_holdem.ai.shark_ai import SharkAI


@dataclass
class LossHandRecord:
    """输牌记录"""
    hand_number: int  # 手牌编号
    street: str  # 街: preflop/flop/turn/river/showdown
    position: str  # 位置
    hole_cards: str  # 手牌
    community_cards: str  # 公共牌
    hand_strength: float  # 手牌强度
    
    # 行动信息
    action_taken: str  # 采取的行动
    amount: int  # 下注金额
    amount_to_call: int  # 需要跟注的金额
    
    # 赔率信息
    pot_size: int  # 底池大小
    pot_odds: float  # 底池赔率
    win_probability: float  # 胜率估计
    
    # 结果
    chips_before: int  # 行动前筹码
    chips_after: int  # 行动后筹码
    chips_lost: int  # 损失的筹码
    
    # 对手信息
    active_opponents: int  # 活跃对手数
    opponent_aggression: str  # 对手激进程度 (高/中/低)


@dataclass
class EliminationRecord:
    """淘汰记录"""
    hand_number: int  # 淘汰手牌
    final_chips: int  # 最终筹码（应为0）
    total_hands: int  # 总局数
    
    # 淘汰前的关键手牌
    key_losses: List[LossHandRecord] = field(default_factory=list)
    
    # 统计摘要
    preflop_losses: int = 0  # 翻牌前输牌数
    flop_losses: int = 0  # 翻牌圈输牌数
    turn_losses: int = 0  # 转牌圈输牌数
    river_losses: int = 0  # 河牌圈输牌数
    
    # 位置统计
    losses_by_position: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    # 行动统计
    losses_by_action: Dict[str, int] = field(default_factory=lambda: defaultdict(int))


class SharkAIAnalyzer:
    """鲨鱼AI输牌分析器"""
    
    def __init__(self):
        self.loss_records: List[LossHandRecord] = []
        self.elimination: Optional[EliminationRecord] = None
        
    def add_loss_record(self, record: LossHandRecord):
        """添加输牌记录"""
        self.loss_records.append(record)
        
    def record_elimination(self, hand_number: int, final_chips: int, total_hands: int):
        """记录淘汰信息"""
        # 取最近的关键输牌（导致筹码大幅减少的）
        key_losses = [r for r in self.loss_records if r.chips_lost >= 50]
        if not key_losses and self.loss_records:
            # 如果没有大损失，取最后3手
            key_losses = self.loss_records[-3:]
        
        # 统计
        preflop = sum(1 for r in self.loss_records if r.street == 'preflop')
        flop = sum(1 for r in self.loss_records if r.street == 'flop')
        turn = sum(1 for r in self.loss_records if r.street == 'turn')
        river = sum(1 for r in self.loss_records if r.street == 'river')
        
        pos_stats = defaultdict(int)
        action_stats = defaultdict(int)
        for r in self.loss_records:
            pos_stats[r.position] += 1
            action_stats[r.action_taken] += 1
        
        self.elimination = EliminationRecord(
            hand_number=hand_number,
            final_chips=final_chips,
            total_hands=total_hands,
            key_losses=key_losses[-5:],  # 最近5手关键输牌
            preflop_losses=preflop,
            flop_losses=flop,
            turn_losses=turn,
            river_losses=river,
            losses_by_position=dict(pos_stats),
            losses_by_action=dict(action_stats)
        )
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        if not self.loss_records:
            return {"message": "本局无输牌记录"}
        
        total_lost = sum(r.chips_lost for r in self.loss_records)
        avg_loss = total_lost / len(self.loss_records) if self.loss_records else 0
        
        # 按街统计
        street_stats = defaultdict(lambda: {'count': 0, 'total_lost': 0})
        for r in self.loss_records:
            street_stats[r.street]['count'] += 1
            street_stats[r.street]['total_lost'] += r.chips_lost
        
        # 按位置统计
        position_stats = defaultdict(lambda: {'count': 0, 'total_lost': 0})
        for r in self.loss_records:
            position_stats[r.position]['count'] += 1
            position_stats[r.position]['total_lost'] += r.chips_lost
        
        # 按行动统计
        action_stats = defaultdict(lambda: {'count': 0, 'total_lost': 0, 'avg_strength': []})
        for r in self.loss_records:
            action_stats[r.action_taken]['count'] += 1
            action_stats[r.action_taken]['total_lost'] += r.chips_lost
            action_stats[r.action_taken]['avg_strength'].append(r.hand_strength)
        
        # 计算平均手牌强度
        for action in action_stats:
            strengths = action_stats[action]['avg_strength']
            action_stats[action]['avg_strength'] = sum(strengths) / len(strengths) if strengths else 0
        
        return {
            'total_losses': len(self.loss_records),
            'total_chips_lost': total_lost,
            'avg_loss_per_hand': avg_loss,
            'street_breakdown': dict(street_stats),
            'position_breakdown': dict(position_stats),
            'action_breakdown': dict(action_stats),
            'elimination': self.elimination
        }
    
    def print_detailed_report(self):
        """打印详细报告"""
        summary = self.get_analysis_summary()
        
        print("\n  【输牌详细分析】")
        print("  " + "-" * 50)
        
        if not self.loss_records:
            print("  本局未记录到输牌数据")
            return
        
        print(f"  总输牌次数: {summary['total_losses']}")
        print(f"  总损失筹码: {summary['total_chips_lost']}")
        print(f"  平均每手损失: {summary['avg_loss_per_hand']:.0f}")
        
        # 按街统计
        print("\n  【各街段输牌分布】")
        for street, data in summary['street_breakdown'].items():
            print(f"    {street:10s}: {data['count']:3d}次, 损失{data['total_lost']:5d}筹码")
        
        # 按位置统计
        print("\n  【各位置输牌分布】")
        for pos, data in sorted(summary['position_breakdown'].items()):
            print(f"    {pos:10s}: {data['count']:3d}次, 损失{data['total_lost']:5d}筹码")
        
        # 按行动统计
        print("\n  【各行动输牌分布】")
        for action, data in sorted(summary['action_breakdown'].items()):
            avg_str = data['avg_strength']
            print(f"    {action:10s}: {data['count']:3d}次, 损失{data['total_lost']:5d}筹码, 平均牌力{avg_str:.2f}")
        
        # 淘汰信息
        if self.elimination:
            print("\n  【淘汰分析】")
            print(f"    淘汰手牌: 第{self.elimination.hand_number}手")
            print(f"    关键输牌（导致淘汰的手牌）:")
            for i, loss in enumerate(self.elimination.key_losses, 1):
                print(f"      {i}. 第{loss.hand_number}手 {loss.street} - {loss.action_taken} "
                      f"手牌{loss.hole_cards} 牌力{loss.hand_strength:.2f} "
                      f"损失{loss.chips_lost}筹码")
        
        print("  " + "-" * 50)


class AutoGameTester:
    """自动化游戏测试器"""
    
    def __init__(self, num_hands: int = 100, num_players: int = 6):
        self.num_hands = num_hands
        self.num_players = num_players
        self.engine = None
        self.ai_engine = AIEngine()
        self.shark_ai = None
        self.analyzer = SharkAIAnalyzer()
        
        self.results = {
            'hands_played': 0,
            'shark_chips_start': 0,
            'shark_chips_end': 0,
            'shark_profit': 0,
            'hands_won': 0,
            'showdowns': 0,
            'folds': 0,
            'vpip_count': 0,
            'pfr_count': 0,
            'eliminated': False,
            'eliminated_at_hand': 0,
            'final_rank': 0,
        }
        
        # 每手牌的记录标志
        self._hand_vpip_recorded = False
        self._hand_pfr_recorded = False
        
        # 当前手牌信息
        self._current_hand_info = {}
        
    def setup_game(self):
        """设置游戏"""
        player_names = ['电脑1号[鲨鱼]', '电脑2号[紧凶]', '电脑3号[松凶]', 
                       '电脑4号[紧弱]', '电脑5号[松弱]', '电脑6号[紧凶]']
        
        self.engine = GameEngine(player_names, initial_chips=1000)
        
        style_map = {
            '紧凶': 'TAG',
            '松凶': 'LAG', 
            '紧弱': 'LAP',
            '松弱': 'LP',
            '鲨鱼': 'SHARK'
        }
        
        for player in self.engine.players:
            player.is_ai = True
            if '[' in player.name and ']' in player.name:
                cn_style = player.name.split('[')[1].split(']')[0]
                player.ai_style = style_map.get(cn_style, 'LAG')
            else:
                player.ai_style = 'LAG'
        
        self.shark_ai = SharkAI()
        self.shark_ai.initialize_opponents(self.engine.players)
        
        shark = self._get_shark_player()
        if shark:
            self.results['shark_chips_start'] = shark.chips
    
    def _get_shark_player(self) -> Optional[Player]:
        """获取鲨鱼AI玩家"""
        for player in self.engine.game_state.players:
            if getattr(player, 'ai_style', '') == 'SHARK':
                return player
        return None
    
    def _get_position_name(self, player: Player) -> str:
        """获取位置名称"""
        # 根据玩家标记判断位置
        if getattr(player, 'is_dealer', False):
            return "BTN(庄家)"
        elif getattr(player, 'is_small_blind', False):
            return "SB(小盲)"
        elif getattr(player, 'is_big_blind', False):
            return "BB(大盲)"
        else:
            # 根据其他玩家位置推断
            gs = self.engine.game_state
            players = gs.players
            num_players = len(players)
            
            # 找到庄家位置
            dealer_idx = -1
            for i, p in enumerate(players):
                if getattr(p, 'is_dealer', False):
                    dealer_idx = i
                    break
            
            if dealer_idx == -1:
                return "未知"
            
            player_idx = players.index(player)
            rel_pos = (player_idx - dealer_idx) % num_players
            
            # 6人桌位置映射
            if num_players == 6:
                pos_map = {3: "UTG(枪口位)", 4: "MP(中间位)", 5: "CO(cutoff)"}
            else:
                # 通用映射
                if rel_pos == num_players - 1:
                    return "CO(cutoff)"
                elif rel_pos >= num_players - 2:
                    return "MP(中间位)"
                else:
                    return "EP(早位)"
            
            return pos_map.get(rel_pos, "未知")
    
    def _cards_to_str(self, cards) -> str:
        """将牌转换为字符串"""
        if not cards:
            return "无"
        return " ".join([f"{c.rank}{c.suit}" for c in cards])
    
    def _get_opponent_aggression(self) -> str:
        """评估对手激进程度"""
        gs = self.engine.game_state
        active = [p for p in gs.players if p.is_active and getattr(p, 'ai_style', '') != 'SHARK']
        
        if not active:
            return "低"
        
        # 根据对手风格判断
        aggressive_count = sum(1 for p in active if getattr(p, 'ai_style', '') in ['LAG', 'TAG'])
        ratio = aggressive_count / len(active)
        
        if ratio > 0.6:
            return "高"
        elif ratio > 0.3:
            return "中"
        return "低"
    
    def _record_loss_if_any(self, hand_num: int, street: str):
        """记录输牌（如果有损失）"""
        shark = self._get_shark_player()
        if not shark:
            return
        
        # 获取之前记录的筹码
        prev_chips = self._current_hand_info.get('chips_before', shark.chips)
        current_chips = shark.chips
        
        chips_lost = prev_chips - current_chips
        
        # 如果损失了筹码，记录
        if chips_lost > 0:
            gs = self.engine.game_state
            hole_cards = shark.hand.cards if shark.hand else []
            community = gs.table.community_cards if hasattr(gs, 'table') else []
            
            # 计算手牌强度
            hand_strength = self.ai_engine.evaluate_hand_strength(hole_cards, community)
            
            # 获取活跃对手数
            active_opps = len([p for p in gs.players if p.is_active and p != shark])
            
            record = LossHandRecord(
                hand_number=hand_num,
                street=street,
                position=self._current_hand_info.get('position', '未知'),
                hole_cards=self._cards_to_str(hole_cards),
                community_cards=self._cards_to_str(community),
                hand_strength=hand_strength,
                action_taken=self._current_hand_info.get('last_action', '未知'),
                amount=self._current_hand_info.get('last_amount', 0),
                amount_to_call=self._current_hand_info.get('amount_to_call', 0),
                pot_size=self._current_hand_info.get('pot_size', 0),
                pot_odds=self._current_hand_info.get('pot_odds', 0),
                win_probability=self._current_hand_info.get('win_prob', 0),
                chips_before=prev_chips,
                chips_after=current_chips,
                chips_lost=chips_lost,
                active_opponents=active_opps,
                opponent_aggression=self._get_opponent_aggression()
            )
            
            self.analyzer.add_loss_record(record)
        
        # 更新当前筹码作为下一轮的基准
        self._current_hand_info['chips_before'] = shark.chips
    
    def _get_ai_action(self, player: Player) -> tuple:
        """获取AI行动"""
        game_state = self.engine.game_state
        betting_round = self.engine.betting_round
        
        if not betting_round:
            return None, 0
        
        available_actions = betting_round.get_available_actions(player)
        if not available_actions:
            return None, 0
        
        amount_to_call = betting_round.get_amount_to_call(player)
        
        hole_cards = player.hand.cards if player.hand else []
        community_cards = game_state.table.community_cards
        
        hand_strength = self.ai_engine.evaluate_hand_strength(hole_cards, community_cards)
        win_prob = hand_strength
        
        total_pot = game_state.table.total_pot if hasattr(game_state.table, 'total_pot') else 0
        pot_odds = self.ai_engine.calculate_pot_odds(total_pot, amount_to_call) if amount_to_call > 0 else 0
        
        ev = self.ai_engine.calculate_expected_value(hand_strength, pot_odds, amount_to_call, total_pot)
        
        # 如果是鲨鱼AI，记录当前信息
        if player.ai_style == 'SHARK' and self.shark_ai:
            self._current_hand_info.update({
                'position': self._get_position_name(player),
                'amount_to_call': amount_to_call,
                'pot_size': total_pot,
                'pot_odds': pot_odds,
                'win_prob': win_prob,
                'hand_strength': hand_strength,
                'chips_before': player.chips
            })
            return self.shark_ai.get_action(player, betting_round, hand_strength, win_prob, pot_odds, ev)
        
        return self.ai_engine.get_action(player, betting_round, hand_strength, win_prob, pot_odds, ev)
    
    def _track_action(self, player: Player, action: str, amount: int, success: bool = True):
        """追踪行动"""
        if player.ai_style != 'SHARK':
            return
        
        if not success:
            return
        
        game_state = self.engine.game_state
        
        # 记录鲨鱼AI的行动
        self._current_hand_info['last_action'] = action
        self._current_hand_info['last_amount'] = amount
        
        # VPIP/PFR统计
        if game_state.state == GameState.PRE_FLOP and action not in ['fold'] and not self._hand_vpip_recorded:
            self.results['vpip_count'] += 1
            self._hand_vpip_recorded = True
        
        if game_state.state == GameState.PRE_FLOP and action in ['raise', 'bet'] and not self._hand_pfr_recorded:
            self.results['pfr_count'] += 1
            self._hand_pfr_recorded = True
        
        if action == 'fold':
            self.results['folds'] += 1
    
    def _process_betting_round(self, hand_num: int, street: str) -> bool:
        """处理下注轮"""
        betting_round = self.engine.betting_round
        game_state = self.engine.game_state
        
        max_actions = 100
        action_count = 0
        
        while not game_state.is_betting_round_complete() and action_count < max_actions:
            current_player = game_state.get_current_player()
            if not current_player or not current_player.is_active:
                game_state.next_player()
                action_count += 1
                continue
            
            action, amount = self._get_ai_action(current_player)
            if action is None:
                game_state.next_player()
                action_count += 1
                continue
            
            action_str = action.name.lower() if hasattr(action, 'name') else str(action).lower()
            
            # 更新鲨鱼AI的对手追踪
            if self.shark_ai and getattr(current_player, 'ai_style', '') != 'SHARK':
                street_name = game_state.state.name.lower() if hasattr(game_state.state, 'name') else str(game_state.state).lower()
                self.shark_ai.update_after_action(current_player.name, action_str, street_name)
            
            # 执行行动
            success, message, bet_amount = betting_round.process_action(current_player, action, amount)
            action_count += 1
            if not success:
                if current_player.is_active:
                    current_player.fold()
                    game_state.update_active_players()
                game_state.next_player()
                continue
            
            # 记录行动
            self._track_action(current_player, action_str, amount)
            
            # 检查是否只剩一个玩家
            if len([p for p in game_state.players if p.is_active]) <= 1:
                return False
        
        # 记录本街的输牌
        self._record_loss_if_any(hand_num, street)
        
        # 收集下注
        betting_round.collect_bets()
        return True
    
    def run_hand(self, hand_num: int) -> bool:
        """运行一手牌"""
        try:
            # 检查鲨鱼是否被淘汰
            shark = self._get_shark_player()
            if not shark or shark.chips <= 0:
                self.results['eliminated'] = True
                if self.results['eliminated_at_hand'] == 0:
                    self.results['eliminated_at_hand'] = hand_num - 1
                return False
            
            # 重置手牌信息
            self._current_hand_info = {'chips_before': shark.chips}
            self._hand_vpip_recorded = False
            self._hand_pfr_recorded = False
            
            # 开始新一手
            self.engine.start_new_hand()
            self.results['hands_played'] += 1
            
            # 翻牌前
            if not self._process_betting_round(hand_num, 'preflop'):
                return True
            
            if len([p for p in self.engine.game_state.players if p.is_active]) <= 1:
                return True
            
            # 发翻牌
            self.engine.deal_flop()
            self.engine.game_state.advance_stage()
            if not self._process_betting_round(hand_num, 'flop'):
                return True
            
            if len([p for p in self.engine.game_state.players if p.is_active]) <= 1:
                return True
            
            # 发转牌
            self.engine.deal_turn()
            self.engine.game_state.advance_stage()
            if not self._process_betting_round(hand_num, 'turn'):
                return True
            
            if len([p for p in self.engine.game_state.players if p.is_active]) <= 1:
                return True
            
            # 发河牌
            self.engine.deal_river()
            self.engine.game_state.advance_stage()
            if not self._process_betting_round(hand_num, 'river'):
                return True
            
            # 记录showdown的损失
            self._record_loss_if_any(hand_num, 'showdown')
            
            return True
            
        except Exception as e:
            print(f"  [错误] 手牌运行错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def run_test(self) -> Dict:
        """运行完整测试"""
        self.setup_game()
        
        for hand_num in range(1, self.num_hands + 1):
            if not self.run_hand(hand_num):
                if self.results['eliminated']:
                    # 记录淘汰信息
                    shark = self._get_shark_player()
                    final_chips = shark.chips if shark else 0
                    self.analyzer.record_elimination(hand_num - 1, final_chips, hand_num - 1)
                    break
        
        self._calculate_final_results()
        return self.results
    
    def _calculate_final_results(self):
        """计算最终结果"""
        shark = self._get_shark_player()
        if shark:
            self.results['shark_chips_end'] = shark.chips
            self.results['shark_profit'] = shark.chips - self.results['shark_chips_start']
        
        # 计算排名
        all_players = [(p.name, p.chips) for p in self.engine.game_state.players]
        all_players.sort(key=lambda x: x[1], reverse=True)
        
        for rank, (name, chips) in enumerate(all_players, 1):
            if '鲨鱼' in name or 'SHARK' in name:
                self.results['final_rank'] = rank
                break
        
        # 计算VPIP/PFR
        if self.results['hands_played'] > 0:
            self.results['vpip'] = self.results['vpip_count'] / self.results['hands_played']
            self.results['pfr'] = self.results['pfr_count'] / self.results['hands_played']


def run_multiple_tests(num_tests: int = 3, num_hands: int = 100):
    """运行多次测试并汇总"""
    all_analyzers = []
    all_results = []
    
    print("\n" + "=" * 70)
    print("  鲨鱼AI输牌分析报告")
    print("  " + f"测试配置: {num_tests}局 x 最多{num_hands}手")
    print("=" * 70)
    
    for test_num in range(1, num_tests + 1):
        print(f"\n\n【第{test_num}局】")
        print("-" * 50)
        
        tester = AutoGameTester(num_hands=num_hands, num_players=6)
        results = tester.run_test()
        all_results.append(results)
        all_analyzers.append(tester.analyzer)
        
        # 打印本局摘要
        print(f"\n  总局数: {results['hands_played']}")
        print(f"  最终筹码: {results['shark_chips_end']}")
        print(f"  盈亏: {results['shark_profit']:+d}")
        print(f"  排名: {results['final_rank']}/{6}")
        print(f"  VPIP: {results.get('vpip', 0)*100:.1f}%")
        print(f"  PFR: {results.get('pfr', 0)*100:.1f}%")
        
        # 打印输牌详细分析
        tester.analyzer.print_detailed_report()
    
    # ========== 汇总报告 ==========
    print("\n\n" + "=" * 70)
    print("【三局汇总分析报告】")
    print("=" * 70)
    
    # 整体统计
    total_profit = sum(r['shark_profit'] for r in all_results)
    avg_profit = total_profit / num_tests
    total_hands = sum(r['hands_played'] for r in all_results)
    avg_hands = total_hands / num_tests
    
    wins = sum(1 for r in all_results if r['shark_profit'] > 0)
    survivals = sum(1 for r in all_results if not r['eliminated'])
    eliminations = num_tests - survivals
    
    print(f"\n【整体表现】")
    print(f"  总盈亏: {total_profit:+d} 筹码")
    print(f"  平均每局盈亏: {avg_profit:+.0f} 筹码")
    print(f"  平均每局手数: {avg_hands:.1f}")
    print(f"  盈利局数: {wins}/{num_tests} ({100*wins/num_tests:.0f}%)")
    print(f"  存活局数: {survivals}/{num_tests} ({100*survivals/num_tests:.0f}%)")
    print(f"  淘汰局数: {eliminations}/{num_tests} ({100*eliminations/num_tests:.0f}%)")
    
    # 汇总所有输牌数据
    print(f"\n【输牌模式分析】")
    
    all_losses = []
    for analyzer in all_analyzers:
        all_losses.extend(analyzer.loss_records)
    
    if all_losses:
        total_losses = len(all_losses)
        total_chips_lost = sum(l.chips_lost for l in all_losses)
        
        print(f"  总输牌次数: {total_losses}")
        print(f"  总损失筹码: {total_chips_lost}")
        print(f"  平均每手损失: {total_chips_lost/total_losses:.0f} 筹码")
        
        # 按街统计
        street_losses = defaultdict(lambda: {'count': 0, 'chips': 0})
        for loss in all_losses:
            street_losses[loss.street]['count'] += 1
            street_losses[loss.street]['chips'] += loss.chips_lost
        
        print(f"\n  各街段输牌分布:")
        for street in ['preflop', 'flop', 'turn', 'river', 'showdown']:
            if street in street_losses:
                data = street_losses[street]
                pct = 100 * data['count'] / total_losses
                print(f"    {street:12s}: {data['count']:3d}次 ({pct:4.1f}%) 损失{data['chips']:5d}筹码")
        
        # 按位置统计
        pos_losses = defaultdict(lambda: {'count': 0, 'chips': 0})
        for loss in all_losses:
            pos_losses[loss.position]['count'] += 1
            pos_losses[loss.position]['chips'] += loss.chips_lost
        
        print(f"\n  各位置输牌分布:")
        for pos, data in sorted(pos_losses.items(), key=lambda x: -x[1]['count']):
            pct = 100 * data['count'] / total_losses
            print(f"    {pos:12s}: {data['count']:3d}次 ({pct:4.1f}%) 损失{data['chips']:5d}筹码")
        
        # 按行动统计
        action_losses = defaultdict(lambda: {'count': 0, 'chips': 0, 'strengths': []})
        for loss in all_losses:
            action_losses[loss.action_taken]['count'] += 1
            action_losses[loss.action_taken]['chips'] += loss.chips_lost
            action_losses[loss.action_taken]['strengths'].append(loss.hand_strength)
        
        print(f"\n  各行动输牌分布:")
        for action, data in sorted(action_losses.items(), key=lambda x: -x[1]['count']):
            pct = 100 * data['count'] / total_losses
            avg_str = sum(data['strengths']) / len(data['strengths']) if data['strengths'] else 0
            print(f"    {action:12s}: {data['count']:3d}次 ({pct:4.1f}%) 损失{data['chips']:5d}筹码 平均牌力{avg_str:.2f}")
        
        # 大损失分析 (>100筹码)
        big_losses = [l for l in all_losses if l.chips_lost >= 100]
        if big_losses:
            print(f"\n  大损失分析(>=100筹码): {len(big_losses)}次")
            for loss in big_losses[:5]:  # 只显示前5个
                print(f"    第{loss.hand_number:3d}手 {loss.street:8s} {loss.position:12s} "
                      f"行动:{loss.action_taken:6s} 手牌:{loss.hole_cards:8s} "
                      f"牌力:{loss.hand_strength:.2f} 损失:{loss.chips_lost:4d}")
    
    # 淘汰分析
    eliminations_data = [a.elimination for a in all_analyzers if a.elimination]
    if eliminations_data:
        print(f"\n【淘汰分析】")
        avg_elim_hand = sum(e.hand_number for e in eliminations_data) / len(eliminations_data)
        print(f"  平均淘汰手牌: 第{avg_elim_hand:.0f}手")
        print(f"  各局淘汰手牌: " + ", ".join([f"第{e.hand_number}手" for e in eliminations_data]))
    
    # 策略改进建议
    print(f"\n【策略改进建议】")
    if all_losses:
        # 找出问题最大的方面
        max_street = max(street_losses.items(), key=lambda x: x[1]['count'])
        max_pos = max(pos_losses.items(), key=lambda x: x[1]['count'])
        max_action = max(action_losses.items(), key=lambda x: x[1]['count'])
        
        print(f"  1. {max_street[0]}阶段输牌最多({max_street[1]['count']}次)，建议检查该阶段的决策逻辑")
        print(f"  2. {max_pos[0]}位置输牌最多({max_pos[1]['count']}次)，建议调整该位置的起手牌范围")
        print(f"  3. {max_action[0]}行动输牌最多({max_action[1]['count']}次)，建议重新评估该行动的适用场景")
        
        # 根据具体数据给出建议
        call_losses = action_losses.get('call', {'count': 0})
        if call_losses['count'] > total_losses * 0.4:
            print(f"  4. 跟注(call)损失过多，可能存在'追牌过度'问题，建议收紧跟注范围")
        
        raise_losses = action_losses.get('raise', {'count': 0})
        if raise_losses['count'] > total_losses * 0.3:
            print(f"  5. 加注(raise)损失过多，可能存在'诈唬过度'问题，建议减少诈唬频率")
    
    print("\n" + "=" * 70)
    
    return all_results, all_analyzers


if __name__ == '__main__':
    # 运行3局测试
    results, analyzers = run_multiple_tests(num_tests=3, num_hands=100)
