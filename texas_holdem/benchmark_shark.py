"""
鲨鱼AI强度测试 - 6AI自动对战100手
统计鲨鱼AI的胜率和盈利能力
"""

import sys
import random
import io
from contextlib import redirect_stdout
from typing import List, Dict, Any
from collections import defaultdict

sys.path.insert(0, 'd:\\workspace\\Texes')

from texas_holdem.game.game_engine import GameEngine
from texas_holdem.game.game_state import GameState
from texas_holdem.ai.ai_engine import AIEngine
from texas_holdem.ai.shark_ai import SharkAI
from texas_holdem.utils.constants import INITIAL_CHIPS, GameState as GS


class SilentGameRunner:
    """静默运行游戏，不输出到控制台"""
    
    def __init__(self, max_hands: int = 10000):
        """
        初始化测试运行器
        
        Args:
            max_hands: 最大手牌数（防止无限循环），默认10000手
        """
        self.max_hands = max_hands
        self.ai_engine = AIEngine()
        self.shark_ai = SharkAI()
        
        # 盲注升级设置
        self.blind_level = 1  # 当前盲注级别
        self.hands_per_level = 100  # 每100手升级一次
        self.base_small_blind = 10   # 初始小盲
        self.base_big_blind = 20     # 初始大盲
        
        # 统计结果
        self.shark_stats = {
            'hands_played': 0,
            'hands_won': 0,
            'showdowns': 0,
            'showdown_wins': 0,
            'wins_without_showdown': 0,
            'final_chips': 0,
            'profit': 0,
            'vpip_count': 0,
            'pfr_count': 0,
            'folds': 0,
            'eliminated': False,
            'eliminated_at': 0,
            'final_rank': 0,
            
            # === 新增详细统计 ===
            # 3bet统计
            'three_bet_opportunities': 0,  # 有3bet机会的次数（有人加注，鲨鱼可以再加注）
            'three_bet_count': 0,          # 实际3bet的次数
            'faced_3bet_count': 0,         # 面对3bet的次数
            'fold_to_3bet_count': 0,       # 面对3bet弃牌的次数
            'call_3bet_count': 0,          # 面对3bet跟注的次数
            'four_bet_count': 0,           # 4bet的次数
            
            # CBet统计（持续下注）
            'cbet_opportunities': 0,       # 翻牌前加注后，翻牌圈率先行动的机会
            'cbet_count': 0,               # 实际CBet次数
            'cbet_success_count': 0,       # CBet成功让对手弃牌的次数
            
            # 位置统计
            'vpip_by_position': defaultdict(int),  # 各位置VPIP计数
            'pfr_by_position': defaultdict(int),   # 各位置PFR计数
            'hands_by_position': defaultdict(int), # 各位置手牌数
            
            # 街继续率
            'saw_flop_count': 0,           # 看到翻牌的次数
            'saw_turn_count': 0,           # 看到转牌的次数
            'saw_river_count': 0,          # 看到河牌的次数
            'fold_flop_count': 0,          # 翻牌圈弃牌次数
            'fold_turn_count': 0,          # 转牌圈弃牌次数
            'fold_river_count': 0,         # 河牌圈弃牌次数
            
            # 下注大小统计
            'total_bets': 0,               # 总下注次数
            'total_bet_amount': 0,         # 总下注金额
            'total_raises': 0,             # 总加注次数
            'total_raise_amount': 0,       # 总加注金额
            'all_in_count': 0,             # All-in次数
            'all_in_wins': 0,              # All-in获胜次数
            
            # 底池统计
            'total_pots_won': 0,           # 赢得底池总数
            'avg_pot_won': 0,              # 平均赢得底池大小
            'largest_pot_won': 0,          # 最大赢得底池
            
            # 偷盲统计
            'steal_attempts': 0,           # 偷盲尝试次数（CO/BTN/SB位置加注）
            'steal_success': 0,            # 偷盲成功次数
            'bb_defend_count': 0,          # 大盲防守次数
            'bb_defend_success': 0,        # 大盲防守成功次数
            
            # 手牌强度统计
            'premium_hands': 0,            # 超强牌次数(AA,KK,QQ,AKs)
            'strong_hands': 0,             # 强牌次数(JJ,TT,AQs,AKo等)
            'playable_hands': 0,           # 可玩牌次数(中等对子,同花高牌等)
            'weak_hands': 0,               # 弱牌次数
            'premium_win_rate': 0,         # 超强牌胜率
            'strong_win_rate': 0,          # 强牌胜率
            'playable_win_rate': 0,        # 可玩牌胜率
            'weak_win_rate': 0,            # 弱牌胜率
            
            # 诈唬统计（基于鲨鱼AI的手牌评估）
            'bluff_attempts': 0,           # 诈唬尝试次数（弱牌激进下注）
            'bluff_success': 0,            # 诈唬成功次数
            'bluff_at_showdown': 0,        # 摊牌时被发现诈唬次数
            
            # 跟注统计
            'call_count': 0,               # 跟注次数
            'call_win_count': 0,           # 跟注后获胜次数
            'call_bet_count': 0,           # 跟注下注次数
            
            # 翻牌圈统计
            'flop_bets': 0,                # 翻牌圈下注次数
            'flop_raises': 0,              # 翻牌圈加注次数
            'flop_calls': 0,               # 翻牌圈跟注次数
            'flop_folds': 0,               # 翻牌圈弃牌次数
            
            # 转牌圈统计
            'turn_bets': 0,
            'turn_raises': 0,
            'turn_calls': 0,
            'turn_folds': 0,
            
            # 河牌圈统计
            'river_bets': 0,
            'river_raises': 0,
            'river_calls': 0,
            'river_folds': 0,
            
            # 摊牌详细统计
            'showdown_losses': 0,          # 摊牌失败次数
            'showdown_checkdown': 0,       # 免费看牌到摊牌次数
        }
        
        # 每手牌的结果记录
        self.hand_results = []
        
        # VPIP/PFR跟踪（每手牌重置）
        self.hand_vpip_recorded = False
        self.hand_pfr_recorded = False
        self.hand_3bet_recorded = False
        
        # 当前手牌临时数据
        self.current_hand = {
            'shark_position': '',          # 鲨鱼位置
            'shark_hand_rank': '',         # 鲨鱼手牌强度
            'preflop_raiser': False,       # 是否是翻牌前加注者
            'current_street': '',          # 当前街
            'pot_before_showdown': 0,      # 摊牌前底池大小
        }
        
    def setup_game(self):
        """设置游戏 - 6个AI玩家"""
        player_names = [
            '电脑1号[鲨鱼]',
            '电脑2号[松凶]', 
            '电脑3号[紧凶]',
            '电脑4号[紧弱]',
            '电脑5号[松弱]',
            '电脑6号[紧凶]'
        ]
        
        self.engine = GameEngine(player_names, INITIAL_CHIPS)
        
        # 设置AI风格
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
        
        # 初始化鲨鱼AI
        self.shark_ai.initialize_opponents(self.engine.players)
        
        # 获取鲨鱼初始筹码
        shark = self._get_shark()
        if shark:
            self.shark_start_chips = shark.chips
            
    def _get_shark(self):
        """获取鲨鱼玩家"""
        for p in self.engine.players:
            if getattr(p, 'ai_style', '') == 'SHARK':
                return p
        return None
    
    def _get_shark_position(self, shark) -> str:
        """获取鲨鱼的位置"""
        if shark.is_dealer:
            return 'BTN'
        elif shark.is_small_blind:
            return 'SB'
        elif shark.is_big_blind:
            return 'BB'
        else:
            # 根据玩家数计算位置
            active_players = [p for p in self.engine.players if p.chips > 0]
            player_count = len(active_players)
            
            # 找到鲨鱼的索引
            for i, p in enumerate(self.engine.players):
                if p.name == shark.name:
                    # 6人桌: BTN, SB, BB, UTG, MP, CO
                    if player_count == 6:
                        if i == 0: return 'BTN'
                        elif i == 1: return 'SB'
                        elif i == 2: return 'BB'
                        elif i == 3: return 'UTG'
                        elif i == 4: return 'MP'
                        else: return 'CO'
                    elif player_count == 5:
                        if i == 0: return 'BTN'
                        elif i == 1: return 'SB'
                        elif i == 2: return 'BB'
                        elif i == 3: return 'UTG'
                        else: return 'CO'
                    elif player_count == 4:
                        if i == 0: return 'BTN'
                        elif i == 1: return 'SB'
                        elif i == 2: return 'BB'
                        else: return 'UTG'
                    elif player_count == 3:
                        if i == 0: return 'BTN'
                        elif i == 1: return 'SB'
                        else: return 'BB'
                    elif player_count == 2:
                        if i == 0: return 'BTN/SB'
                        else: return 'BB'
                    break
        return 'Unknown'
    
    def _classify_hand(self, hole_cards) -> str:
        """分类手牌强度"""
        if not hole_cards or len(hole_cards) != 2:
            return 'weak'
        
        from texas_holdem.core.card import Card
        
        c1, c2 = hole_cards
        rank1, rank2 = c1.rank, c2.rank
        suited = c1.suit == c2.suit
        
        # 超强牌: AA, KK, QQ, AKs
        premium_pairs = ['A', 'K', 'Q']
        if rank1 == rank2 and rank1 in premium_pairs:
            return 'premium'
        if (rank1 == 'A' and rank2 == 'K') or (rank1 == 'K' and rank2 == 'A'):
            if suited:
                return 'premium'
        
        # 强牌: JJ, TT, 99, AQs, AKo, AJs, KQs
        strong_pairs = ['J', 'T', '9']
        if rank1 == rank2 and rank1 in strong_pairs:
            return 'strong'
        
        # 高牌组合
        high_cards = ['A', 'K', 'Q', 'J']
        if rank1 in high_cards and rank2 in high_cards:
            if suited or (rank1 == 'A' or rank2 == 'A'):
                return 'strong'
        
        # 可玩牌: 中等对子, 同花高牌, 连牌
        if rank1 == rank2:
            return 'playable'
        
        rank_values = {'2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9, 'T':10, 'J':11, 'Q':12, 'K':13, 'A':14}
        v1, v2 = rank_values.get(rank1, 0), rank_values.get(rank2, 0)
        gap = abs(v1 - v2)
        
        if suited and gap <= 3:
            return 'playable'
        if gap <= 1 and v1 >= 8 and v2 >= 8:
            return 'playable'
        
        return 'weak'
    
    def _get_ai_action(self, player, betting_round):
        """获取AI行动"""
        from texas_holdem.utils.constants import Action
        
        game_state = betting_round.game_state
        hole_cards = player.hand.cards if player.hand else []
        community_cards = game_state.table.community_cards
        
        hand_strength = self.ai_engine.evaluate_hand_strength(hole_cards, community_cards)
        win_prob = hand_strength
        
        amount_to_call = betting_round.get_amount_to_call(player)
        total_pot = game_state.table.total_pot
        pot_odds = self.ai_engine.calculate_pot_odds(total_pot, amount_to_call) if amount_to_call > 0 else 0
        ev = self.ai_engine.calculate_expected_value(hand_strength, pot_odds, amount_to_call, total_pot)
        
        # 鲨鱼AI使用自己的决策
        if player.ai_style == 'SHARK':
            action, amount = self.shark_ai.get_action(
                player, betting_round, hand_strength, win_prob, pot_odds, ev
            )
        else:
            # 其他AI使用标准引擎
            action, amount = self.ai_engine.get_action(
                player, betting_round, hand_strength, win_prob, pot_odds, ev
            )
        
        return action, amount, hand_strength
    
    def run_hand(self, hand_num: int) -> bool:
        """运行一手牌"""
        try:
            # 检查鲨鱼是否被淘汰
            shark = self._get_shark()
            if not shark or shark.chips <= 0:
                if not self.shark_stats['eliminated']:
                    self.shark_stats['eliminated'] = True
                    self.shark_stats['eliminated_at'] = hand_num
                return False
            
            # 开始新一手
            self.engine.start_new_hand()
            self.shark_stats['hands_played'] += 1
            
            # DEBUG: 检查is_preflop_raiser重置
            # print(f"  DEBUG: 新手牌开始，is_preflop_raiser={self.shark_ai.is_preflop_raiser}")
            
            # 检查盲注升级（每1000手翻倍）
            new_level = (hand_num - 1) // self.hands_per_level + 1
            if new_level > self.blind_level:
                self.blind_level = new_level
                multiplier = 2 ** (self.blind_level - 1)  # 2的(级别-1)次方
                import texas_holdem.utils.constants as constants
                constants.SMALL_BLIND = self.base_small_blind * multiplier
                constants.BIG_BLIND = self.base_big_blind * multiplier
                print(f"  *** 盲注升级！第{self.blind_level}级: {constants.SMALL_BLIND}/{constants.BIG_BLIND} ***")
            
            # 每10手牌输出一次进度（用于调试卡顿问题）
            if hand_num % 10 == 0:
                print(f"  进度: 第{hand_num}手牌，鲨鱼筹码: {shark.chips if shark else 0}，盲注: {constants.SMALL_BLIND}/{constants.BIG_BLIND}")
            
            # 重置本手牌跟踪数据（确保每手牌只统计一次）
            self.hand_vpip_recorded = False
            self.hand_pfr_recorded = False
            self.hand_3bet_recorded = False
            self.hand_steal_recorded = False      # 偷盲每手牌只计一次
            self.hand_cbet_recorded = False       # CBet机会每手牌只计一次
            self.hand_bb_defend_recorded = False  # 大盲防守每手牌只计一次
            self.shark_ai.is_preflop_raiser = False  # 重置翻牌前加注者标记
            self.current_hand = {
                'shark_position': self._get_shark_position(shark),
                'shark_hand_rank': self._classify_hand(shark.hand.cards if shark.hand else []),
                'preflop_raiser': False,
                'current_street': 'preflop',
                'pot_before_showdown': 0,
            }
            
            # 记录手牌分类统计
            hand_rank = self.current_hand['shark_hand_rank']
            if hand_rank == 'premium':
                self.shark_stats['premium_hands'] += 1
            elif hand_rank == 'strong':
                self.shark_stats['strong_hands'] += 1
            elif hand_rank == 'playable':
                self.shark_stats['playable_hands'] += 1
            else:
                self.shark_stats['weak_hands'] += 1
            
            # 记录位置统计
            position = self.current_hand['shark_position']
            self.shark_stats['hands_by_position'][position] += 1
            
            # 记录鲨鱼初始筹码
            shark_start_chips = shark.chips if shark else 0
            
            # 运行翻牌前
            if not self._run_betting_round('preflop'):
                self._check_winner(shark_start_chips)
                return True
            
            # DEBUG: 检查翻牌前结束后的状态
            # print(f"  DEBUG: 翻牌前结束，is_preflop_raiser={self.shark_ai.is_preflop_raiser}")
            
            # 翻牌圈
            active = len([p for p in self.engine.players if p.is_active])
            if active > 1:
                self.engine.deal_flop()
                self.engine.game_state.advance_stage()
                self.shark_stats['saw_flop_count'] += 1
                self.current_hand['current_street'] = 'flop'
                if not self._run_betting_round('flop'):
                    self._check_winner(shark_start_chips)
                    return True
            
            # 转牌圈
            active = len([p for p in self.engine.players if p.is_active])
            if active > 1:
                self.engine.deal_turn()
                self.engine.game_state.advance_stage()
                self.shark_stats['saw_turn_count'] += 1
                self.current_hand['current_street'] = 'turn'
                if not self._run_betting_round('turn'):
                    self._check_winner(shark_start_chips)
                    return True
            
            # 河牌圈
            active = len([p for p in self.engine.players if p.is_active])
            if active > 1:
                self.engine.deal_river()
                self.engine.game_state.advance_stage()
                self.shark_stats['saw_river_count'] += 1
                self.current_hand['current_street'] = 'river'
                if not self._run_betting_round('river'):
                    self._check_winner(shark_start_chips)
                    return True
            
            # 摊牌
            self._resolve_showdown(shark_start_chips)
            return True
            
        except Exception as e:
            return False
    
    def _run_betting_round(self, street: str) -> bool:
        """运行下注轮"""
        from texas_holdem.game.betting import BettingRound
        from texas_holdem.utils.constants import Action
        import time
        
        game_state = self.engine.game_state
        betting_round = BettingRound(game_state)
        
        max_actions = 100
        action_count = 0
        start_time = time.time()  # 记录开始时间
        
        # 翻牌前是否有加注（用于3bet统计）
        preflop_raise_happened = False
        facing_preflop_raise = False
        
        loop_count = 0
        while not game_state.is_betting_round_complete() and action_count < max_actions:
            loop_count += 1
            
            # 超时检查：如果一轮下注超过10秒，强制退出
            elapsed = time.time() - start_time
            if elapsed > 10:
                print(f"  警告：{street}轮次超时(10s)，强制结束")
                print(f"    行动次数: {action_count}, 循环次数: {loop_count}")
                print(f"    当前玩家: {game_state.get_current_player()}")
                print(f"    活动玩家: {len(game_state.get_active_players())}")
                break
            
            current_player = game_state.get_current_player()
            if not current_player or not current_player.is_active:
                # 如果没有可行动的玩家，跳出循环
                break
            
            # 防止某个玩家无限决策（每100次循环检查一次）
            if loop_count % 100 == 0:
                print(f"  警告：{street}轮次循环次数过多({loop_count})，当前玩家: {current_player.name}")
            
            # 在行动前检测是否面对加注（用于3bet统计）
            shark = self._get_shark()
            if shark and current_player.name == shark.name and street == 'preflop':
                amount_to_call = betting_round.get_amount_to_call(current_player)
                # 如果需要跟注超过20，说明有人加注了
                if amount_to_call > 20:
                    facing_preflop_raise = True
            
            # 获取行动（带超时保护）
            # print(f"    DEBUG: {current_player.name} 正在决策...")  # 调试用，如需调试可取消注释
            action, amount, hand_strength = self._get_ai_action(current_player, betting_round)
            if action is None:
                game_state.next_player()
                continue
            
            action_str = str(action).lower().replace('action.', '')
            amount_to_call = betting_round.get_amount_to_call(current_player)
            
            # 记录鲨鱼数据
            if shark and current_player.name == shark.name:
                position = self.current_hand['shark_position']
                
                # VPIP: 一手牌只计算一次（首次入池）
                if street == 'preflop' and action_str in ['raise', 'call', 'bet'] and not self.hand_vpip_recorded:
                    self.shark_stats['vpip_count'] += 1
                    self.shark_stats['vpip_by_position'][position] += 1
                    self.hand_vpip_recorded = True
                
                # PFR: 一手牌只计算一次（首次加注）
                if street == 'preflop' and action_str == 'raise' and not self.hand_pfr_recorded:
                    self.shark_stats['pfr_count'] += 1
                    self.shark_stats['pfr_by_position'][position] += 1
                    self.hand_pfr_recorded = True
                    self.current_hand['preflop_raiser'] = True
                
                # 3bet统计（翻牌前）- 修复：现在facing_preflop_raise在行动前已设置
                if street == 'preflop':
                    if action_str == 'raise':
                        if facing_preflop_raise and not self.hand_3bet_recorded:
                            # 这是3bet
                            self.shark_stats['three_bet_count'] += 1
                            self.hand_3bet_recorded = True
                        else:
                            # 这是初始加注，标记为有加注发生
                            preflop_raise_happened = True
                    
                    # 面对加注的统计（每手牌只统计一次机会）
                    if facing_preflop_raise and not self.hand_3bet_recorded:
                        if action_str == 'fold':
                            self.shark_stats['faced_3bet_count'] += 1
                            self.shark_stats['fold_to_3bet_count'] += 1
                            self.shark_stats['three_bet_opportunities'] += 1
                            self.hand_3bet_recorded = True  # 标记已统计
                        elif action_str in ['call', 'bet']:
                            self.shark_stats['faced_3bet_count'] += 1
                            self.shark_stats['call_3bet_count'] += 1
                            self.shark_stats['three_bet_opportunities'] += 1
                            self.hand_3bet_recorded = True  # 标记已统计
                        elif action_str == 'raise':
                            # 已经是3bet，上面统计过了
                            self.shark_stats['three_bet_opportunities'] += 1
                            self.hand_3bet_recorded = True  # 标记已统计
                
                # CBet统计（翻牌圈）
                # 使用 shark_ai.is_preflop_raiser 来判断是否是翻牌前加注者
                    # CBet统计（翻牌圈）
                if street == 'flop' and self.shark_ai.is_preflop_raiser and not self.hand_cbet_recorded:
                    self.hand_cbet_recorded = True
                    self.shark_stats['cbet_opportunities'] += 1
                    if action_str in ['bet', 'raise']:
                        self.shark_stats['cbet_count'] += 1
                
                # 偷盲统计（CO/BTN/SB位置加注）
                # 每手牌只计一次偷盲尝试
                if street == 'preflop' and action_str == 'raise' and not self.hand_steal_recorded:
                    if position in ['CO', 'BTN', 'SB']:
                        self.hand_steal_recorded = True
                        self.shark_stats['steal_attempts'] += 1
                
                # 大盲防守（每手牌只计一次）
                if street == 'preflop' and position == 'BB' and action_str in ['call', 'raise'] and not self.hand_bb_defend_recorded:
                    self.hand_bb_defend_recorded = True
                    self.shark_stats['bb_defend_count'] += 1
                
                # 弃牌统计
                if action_str == 'fold':
                    self.shark_stats['folds'] += 1
                    if street == 'flop':
                        self.shark_stats['fold_flop_count'] += 1
                    elif street == 'turn':
                        self.shark_stats['fold_turn_count'] += 1
                    elif street == 'river':
                        self.shark_stats['fold_river_count'] += 1
                
                # 跟注统计
                if action_str == 'call':
                    self.shark_stats['call_count'] += 1
                
                # All-in统计
                if action_str == 'all_in':
                    self.shark_stats['all_in_count'] += 1
                
                # 下注大小统计
                if action_str == 'bet' and amount > 0:
                    self.shark_stats['total_bets'] += 1
                    self.shark_stats['total_bet_amount'] += amount
                if action_str == 'raise' and amount > 0:
                    self.shark_stats['total_raises'] += 1
                    self.shark_stats['total_raise_amount'] += amount
                
                # 各街行动统计
                if street == 'flop':
                    if action_str == 'bet':
                        self.shark_stats['flop_bets'] += 1
                    elif action_str == 'raise':
                        self.shark_stats['flop_raises'] += 1
                    elif action_str == 'call':
                        self.shark_stats['flop_calls'] += 1
                    elif action_str == 'fold':
                        self.shark_stats['flop_folds'] += 1
                elif street == 'turn':
                    if action_str == 'bet':
                        self.shark_stats['turn_bets'] += 1
                    elif action_str == 'raise':
                        self.shark_stats['turn_raises'] += 1
                    elif action_str == 'call':
                        self.shark_stats['turn_calls'] += 1
                    elif action_str == 'fold':
                        self.shark_stats['turn_folds'] += 1
                elif street == 'river':
                    if action_str == 'bet':
                        self.shark_stats['river_bets'] += 1
                    elif action_str == 'raise':
                        self.shark_stats['river_raises'] += 1
                    elif action_str == 'call':
                        self.shark_stats['river_calls'] += 1
                    elif action_str == 'fold':
                        self.shark_stats['river_folds'] += 1
            
            # 更新鲨鱼AI追踪
            if current_player.ai_style != 'SHARK':
                self.shark_ai.update_after_action(
                    current_player.name, action_str, street
                )
            
            # 执行行动
            success, msg, bet_amount = betting_round.process_action(current_player, action, amount)
            if not success:
                game_state.next_player()
                continue
            
            action_count += 1
            
            # 移动到下一个玩家
            game_state.next_player()
            
            # 更新活动玩家列表（因为可能有玩家弃牌）
            game_state.update_active_players()
            
            # 检查是否只剩一个玩家
            active_players = game_state.get_active_players()
            if len(active_players) <= 1:
                # CBet成功：如果鲨鱼下注/加注后只剩一个玩家
                if shark and current_player.name == shark.name:
                    if street == 'flop' and self.current_hand['preflop_raiser']:
                        if action_str in ['bet', 'raise']:
                            self.shark_stats['cbet_success_count'] += 1
                    # 偷盲成功
                    if street == 'preflop' and self.current_hand['shark_position'] in ['CO', 'BTN', 'SB']:
                        if action_str in ['raise', 'bet', 'all_in']:
                            self.shark_stats['steal_success'] += 1
                return False
        
        # 安全检查：如果达到最大行动次数，强制结束
        if action_count >= max_actions:
            print(f"  警告：达到最大行动次数限制({max_actions})，强制结束当前下注轮")
        
        # 收集下注
        betting_round.collect_bets()
        game_state.advance_stage()
        return True
    
    def _check_winner(self, shark_start_chips: int):
        """检查赢家（不摊牌）"""
        shark = self._get_shark()
        if not shark:
            return
        
        active = [p for p in self.engine.players if p.is_active]
        if len(active) == 1 and active[0].name == shark.name:
            self.shark_stats['hands_won'] += 1
            self.shark_stats['wins_without_showdown'] += 1
            
            # 底池统计
            pot_size = self.engine.game_state.table.total_pot
            self.shark_stats['total_pots_won'] += 1
            self.shark_stats['avg_pot_won'] = (self.shark_stats['avg_pot_won'] * (self.shark_stats['total_pots_won'] - 1) + pot_size) / self.shark_stats['total_pots_won']
            if pot_size > self.shark_stats['largest_pot_won']:
                self.shark_stats['largest_pot_won'] = pot_size
            
            # All-in获胜统计
            if shark.chips <= 0:  # All-in且获胜
                self.shark_stats['all_in_wins'] += 1
            
            # 手牌胜率统计
            hand_rank = self.current_hand['shark_hand_rank']
            if hand_rank == 'premium':
                self.shark_stats['premium_win_rate'] += 1
            elif hand_rank == 'strong':
                self.shark_stats['strong_win_rate'] += 1
            elif hand_rank == 'playable':
                self.shark_stats['playable_win_rate'] += 1
            else:
                self.shark_stats['weak_win_rate'] += 1
    
    def _resolve_showdown(self, shark_start_chips: int):
        """摊牌结算"""
        from texas_holdem.core.evaluator import PokerEvaluator
        
        game_state = self.engine.game_state
        active_players = [p for p in self.engine.players if p.is_active]
        
        if len(active_players) == 0:
            return
        
        shark = self._get_shark()
        
        if len(active_players) == 1:
            winner = active_players[0]
            win_amount = game_state.table.total_pot
            winner.chips += win_amount
            
            if shark and winner.name == shark.name:
                self.shark_stats['hands_won'] += 1
                self.shark_stats['wins_without_showdown'] += 1
                
                # 底池统计
                self.shark_stats['total_pots_won'] += 1
                self.shark_stats['avg_pot_won'] = (self.shark_stats['avg_pot_won'] * (self.shark_stats['total_pots_won'] - 1) + win_amount) / self.shark_stats['total_pots_won']
                if win_amount > self.shark_stats['largest_pot_won']:
                    self.shark_stats['largest_pot_won'] = win_amount
            return
        
        # 比较牌力
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
        
        # 分配底池
        if winners:
            win_amount = game_state.table.total_pot // len(winners)
            for winner in winners:
                winner.chips += win_amount
                
                if shark and winner.name == shark.name:
                    self.shark_stats['hands_won'] += 1
                    self.shark_stats['showdown_wins'] += 1
                    self.shark_stats['showdowns'] += 1
                    
                    # 底池统计
                    self.shark_stats['total_pots_won'] += 1
                    self.shark_stats['avg_pot_won'] = (self.shark_stats['avg_pot_won'] * (self.shark_stats['total_pots_won'] - 1) + win_amount) / self.shark_stats['total_pots_won']
                    if win_amount > self.shark_stats['largest_pot_won']:
                        self.shark_stats['largest_pot_won'] = win_amount
                    
                    # 手牌胜率统计
                    hand_rank = self.current_hand['shark_hand_rank']
                    if hand_rank == 'premium':
                        self.shark_stats['premium_win_rate'] += 1
                    elif hand_rank == 'strong':
                        self.shark_stats['strong_win_rate'] += 1
                    elif hand_rank == 'playable':
                        self.shark_stats['playable_win_rate'] += 1
                    else:
                        self.shark_stats['weak_win_rate'] += 1
                elif shark and winner.name != shark.name and shark in active_players:
                    self.shark_stats['showdown_losses'] += 1
                    self.shark_stats['showdowns'] += 1
    
    def _check_game_over(self) -> tuple:
        """
        检查游戏是否结束（鲨鱼被淘汰或鲨鱼胜出）
        
        Returns:
            (是否结束, 结果类型) 结果类型: 'eliminated', 'victory', 'ongoing'
        """
        shark = self._get_shark()
        
        # 鲨鱼被淘汰
        if not shark or shark.chips <= 0:
            return True, 'eliminated'
        
        # 检查是否只剩鲨鱼AI一个玩家有筹码
        active_with_chips = [p for p in self.engine.players if p.chips > 0]
        if len(active_with_chips) == 1 and active_with_chips[0].name == shark.name:
            return True, 'victory'
        
        return False, 'ongoing'
    
    def run_benchmark(self) -> Dict:
        """
        运行完整测试，直到鲨鱼AI被淘汰或胜出
        盲注级别保持10/20不升级
        """
        print(f"\n{'='*60}")
        print(f"  鲨鱼AI强度测试 - 直到淘汰或胜出")
        print(f"  盲注: 10/20 (固定)")
        print(f"{'='*60}\n")
        
        self.setup_game()
        
        # 使用StringIO抑制输出
        f = io.StringIO()
        hand_num = 0
        
        with redirect_stdout(f):
            while hand_num < self.max_hands:
                hand_num += 1
                
                if hand_num % 10 == 0:
                    print(f"  进度: {hand_num}手牌")
                
                # 先检查游戏是否已经结束
                is_over, result = self._check_game_over()
                if is_over:
                    if result == 'eliminated':
                        print(f"\n  鲨鱼AI在第{hand_num-1}手牌被淘汰！")
                        if not self.shark_stats['eliminated']:
                            self.shark_stats['eliminated'] = True
                            self.shark_stats['eliminated_at'] = hand_num - 1
                    elif result == 'victory':
                        print(f"\n  鲨鱼AI在第{hand_num-1}手牌胜出！成为唯一幸存者！")
                        self.shark_stats['victory'] = True
                        self.shark_stats['victory_at'] = hand_num - 1
                    break
                
                # 运行一手牌
                if not self.run_hand(hand_num):
                    # 检查是否因为鲨鱼被淘汰而结束
                    is_over, result = self._check_game_over()
                    if is_over:
                        if result == 'eliminated':
                            print(f"\n  鲨鱼AI在第{hand_num}手牌被淘汰！")
                            if not self.shark_stats['eliminated']:
                                self.shark_stats['eliminated'] = True
                                self.shark_stats['eliminated_at'] = hand_num
                        elif result == 'victory':
                            print(f"\n  鲨鱼AI在第{hand_num}手牌胜出！成为唯一幸存者！")
                            self.shark_stats['victory'] = True
                            self.shark_stats['victory_at'] = hand_num
                        break
        
        # 计算最终结果
        self._calculate_final_results()
        
        return self.shark_stats
    
    def _calculate_final_results(self):
        """计算最终结果"""
        shark = self._get_shark()
        if shark:
            self.shark_stats['final_chips'] = shark.chips
            self.shark_stats['profit'] = shark.chips - self.shark_start_chips
        
        # 计算排名
        all_players = [(p.name, p.chips) for p in self.engine.players]
        all_players.sort(key=lambda x: x[1], reverse=True)
        
        for rank, (name, chips) in enumerate(all_players, 1):
            if '鲨鱼' in name or 'SHARK' in name:
                self.shark_stats['final_rank'] = rank
                break
        
        # 计算VPIP/PFR
        if self.shark_stats['hands_played'] > 0:
            self.shark_stats['vpip'] = self.shark_stats['vpip_count'] / self.shark_stats['hands_played'] * 100
            self.shark_stats['pfr'] = self.shark_stats['pfr_count'] / self.shark_stats['hands_played'] * 100
        
        # 计算3bet率
        if self.shark_stats['three_bet_opportunities'] > 0:
            self.shark_stats['three_bet_pct'] = self.shark_stats['three_bet_count'] / self.shark_stats['three_bet_opportunities'] * 100
        else:
            self.shark_stats['three_bet_pct'] = 0
        
        # 计算面对3bet的弃牌率
        if self.shark_stats['faced_3bet_count'] > 0:
            self.shark_stats['fold_to_3bet_pct'] = self.shark_stats['fold_to_3bet_count'] / self.shark_stats['faced_3bet_count'] * 100
        else:
            self.shark_stats['fold_to_3bet_pct'] = 0
        
        # 计算CBet率
        if self.shark_stats['cbet_opportunities'] > 0:
            self.shark_stats['cbet_pct'] = self.shark_stats['cbet_count'] / self.shark_stats['cbet_opportunities'] * 100
            self.shark_stats['cbet_success_pct'] = self.shark_stats['cbet_success_count'] / self.shark_stats['cbet_count'] * 100 if self.shark_stats['cbet_count'] > 0 else 0
        else:
            self.shark_stats['cbet_pct'] = 0
            self.shark_stats['cbet_success_pct'] = 0
        
        # 计算平均下注大小
        if self.shark_stats['total_bets'] > 0:
            self.shark_stats['avg_bet_size'] = self.shark_stats['total_bet_amount'] / self.shark_stats['total_bets']
        else:
            self.shark_stats['avg_bet_size'] = 0
        
        if self.shark_stats['total_raises'] > 0:
            self.shark_stats['avg_raise_size'] = self.shark_stats['total_raise_amount'] / self.shark_stats['total_raises']
        else:
            self.shark_stats['avg_raise_size'] = 0
        
        # 计算偷盲率
        if self.shark_stats['steal_attempts'] > 0:
            self.shark_stats['steal_success_pct'] = self.shark_stats['steal_success'] / self.shark_stats['steal_attempts'] * 100
        else:
            self.shark_stats['steal_success_pct'] = 0
        
        # 计算各位置VPIP/PFR
        self.shark_stats['vpip_by_position_pct'] = {}
        self.shark_stats['pfr_by_position_pct'] = {}
        for pos in ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']:
            hands = self.shark_stats['hands_by_position'].get(pos, 0)
            if hands > 0:
                self.shark_stats['vpip_by_position_pct'][pos] = self.shark_stats['vpip_by_position'].get(pos, 0) / hands * 100
                self.shark_stats['pfr_by_position_pct'][pos] = self.shark_stats['pfr_by_position'].get(pos, 0) / hands * 100
            else:
                self.shark_stats['vpip_by_position_pct'][pos] = 0
                self.shark_stats['pfr_by_position_pct'][pos] = 0
        
        # 计算手牌胜率
        if self.shark_stats['premium_hands'] > 0:
            self.shark_stats['premium_win_pct'] = self.shark_stats['premium_win_rate'] / self.shark_stats['premium_hands'] * 100
        else:
            self.shark_stats['premium_win_pct'] = 0
        
        if self.shark_stats['strong_hands'] > 0:
            self.shark_stats['strong_win_pct'] = self.shark_stats['strong_win_rate'] / self.shark_stats['strong_hands'] * 100
        else:
            self.shark_stats['strong_win_pct'] = 0
        
        if self.shark_stats['playable_hands'] > 0:
            self.shark_stats['playable_win_pct'] = self.shark_stats['playable_win_rate'] / self.shark_stats['playable_hands'] * 100
        else:
            self.shark_stats['playable_win_pct'] = 0
        
        if self.shark_stats['weak_hands'] > 0:
            self.shark_stats['weak_win_pct'] = self.shark_stats['weak_win_rate'] / self.shark_stats['weak_hands'] * 100
        else:
            self.shark_stats['weak_win_pct'] = 0
        
        # 计算各街弃牌率
        if self.shark_stats['saw_flop_count'] > 0:
            self.shark_stats['fold_flop_pct'] = self.shark_stats['fold_flop_count'] / self.shark_stats['saw_flop_count'] * 100
        else:
            self.shark_stats['fold_flop_pct'] = 0
        
        if self.shark_stats['saw_turn_count'] > 0:
            self.shark_stats['fold_turn_pct'] = self.shark_stats['fold_turn_count'] / self.shark_stats['saw_turn_count'] * 100
        else:
            self.shark_stats['fold_turn_pct'] = 0
        
        if self.shark_stats['saw_river_count'] > 0:
            self.shark_stats['fold_river_pct'] = self.shark_stats['fold_river_count'] / self.shark_stats['saw_river_count'] * 100
        else:
            self.shark_stats['fold_river_pct'] = 0
    
    def print_report(self, output_file: str = None):
        """
        打印详细测试报告
        
        Args:
            output_file: 输出文件路径，如果指定则写入文件，否则打印到控制台
        """
        import os
        import texas_holdem.utils.constants as constants
        
        s = self.shark_stats
        hands = s['hands_played']
        
        # 构建报告内容
        lines = []
        lines.append(f"\n{'='*60}")
        lines.append(f"  鲨鱼AI详细测试报告")
        lines.append(f"{'='*60}\n")
        
        # === 基础统计 ===
        lines.append(f"  【基础统计】")
        lines.append(f"  测试手牌数:     {hands}手")
        lines.append(f"  盲注级别:       第{self.blind_level}级 ({constants.SMALL_BLIND}/{constants.BIG_BLIND})")
        if s.get('eliminated'):
            lines.append(f"  测试结果:       淘汰 (第{s['eliminated_at']}手)")
        elif s.get('victory'):
            lines.append(f"  测试结果:       胜出 (第{s['victory_at']}手)")
        else:
            lines.append(f"  测试结果:       未结束")
        lines.append(f"  最终排名:       {s['final_rank']}/6")
        lines.append(f"  初始筹码:       {self.shark_start_chips}")
        lines.append(f"  最终筹码:       {s['final_chips']}")
        lines.append(f"  盈亏:           {s['profit']:+d}")
        lines.append(f"  胜率:           {s['hands_won']}/{hands} ({100*s['hands_won']/max(1,hands):.1f}%)")
        
        # === 翻牌前统计 ===
        lines.append(f"\n  【翻牌前统计】")
        lines.append(f"  VPIP:           {s.get('vpip', 0):.1f}% (主动入池率)")
        lines.append(f"  PFR:            {s.get('pfr', 0):.1f}% (翻牌前加注率)")
        lines.append(f"  3Bet:           {s.get('three_bet_pct', 0):.1f}% ({s['three_bet_count']}/{s['three_bet_opportunities']})")
        lines.append(f"  Fold to 3Bet:   {s.get('fold_to_3bet_pct', 0):.1f}% (面对3bet弃牌率)")
        lines.append(f"  4Bet:           {s['four_bet_count']}次")
        
        # === 位置统计 ===
        lines.append(f"\n  【位置统计 - VPIP / PFR】")
        for pos in ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']:
            vpip = s['vpip_by_position_pct'].get(pos, 0)
            pfr = s['pfr_by_position_pct'].get(pos, 0)
            hand_count = s['hands_by_position'].get(pos, 0)
            if hand_count > 0:
                lines.append(f"  {pos:4s}:           {vpip:5.1f}% / {pfr:5.1f}%  ({hand_count}手)")
        
        # === 翻牌后统计 ===
        lines.append(f"\n  【翻牌后统计】")
        lines.append(f"  CBet率:         {s.get('cbet_pct', 0):.1f}% (持续下注率)")
        lines.append(f"  CBet成功率:     {s.get('cbet_success_pct', 0):.1f}% (CBet后立即获胜)")
        lines.append(f"  看到翻牌:       {s['saw_flop_count']}次 ({100*s['saw_flop_count']/max(1,hands):.1f}%)")
        lines.append(f"  看到转牌:       {s['saw_turn_count']}次 ({100*s['saw_turn_count']/max(1,hands):.1f}%)")
        lines.append(f"  看到河牌:       {s['saw_river_count']}次 ({100*s['saw_river_count']/max(1,hands):.1f}%)")
        lines.append(f"  翻牌圈弃牌率:   {s.get('fold_flop_pct', 0):.1f}%")
        lines.append(f"  转牌圈弃牌率:   {s.get('fold_turn_pct', 0):.1f}%")
        lines.append(f"  河牌圈弃牌率:   {s.get('fold_river_pct', 0):.1f}%")
        
        # === 各街行动统计 ===
        lines.append(f"\n  【各街行动统计】")
        lines.append(f"  翻牌圈: 下注{s['flop_bets']} 加注{s['flop_raises']} 跟注{s['flop_calls']} 弃牌{s['flop_folds']}")
        lines.append(f"  转牌圈: 下注{s['turn_bets']} 加注{s['turn_raises']} 跟注{s['turn_calls']} 弃牌{s['turn_folds']}")
        lines.append(f"  河牌圈: 下注{s['river_bets']} 加注{s['river_raises']} 跟注{s['river_calls']} 弃牌{s['river_folds']}")
        
        # === 偷盲统计 ===
        lines.append(f"\n  【偷盲统计】")
        lines.append(f"  偷盲尝试:       {s['steal_attempts']}次")
        lines.append(f"  偷盲成功:       {s['steal_success']}次 ({s.get('steal_success_pct', 0):.1f}%)")
        lines.append(f"  大盲防守:       {s['bb_defend_count']}次")
        
        # === 下注大小统计 ===
        lines.append(f"\n  【下注大小统计】")
        avg_bet = s.get('avg_bet_size', 0)
        avg_raise = s.get('avg_raise_size', 0)
        lines.append(f"  平均下注:       {avg_bet:.0f}筹码")
        lines.append(f"  平均加注:       {avg_raise:.0f}筹码")
        lines.append(f"  All-in次数:     {s['all_in_count']}次")
        
        # === 手牌分类胜率 ===
        lines.append(f"\n  【手牌分类胜率】")
        lines.append(f"  超强牌:         {s['premium_win_pct']:.1f}% ({s['premium_win_rate']}/{s['premium_hands']})")
        lines.append(f"  强牌:           {s['strong_win_pct']:.1f}% ({s['strong_win_rate']}/{s['strong_hands']})")
        lines.append(f"  可玩牌:         {s['playable_win_pct']:.1f}% ({s['playable_win_rate']}/{s['playable_hands']})")
        lines.append(f"  弱牌:           {s['weak_win_pct']:.1f}% ({s['weak_win_rate']}/{s['weak_hands']})")
        
        # === 摊牌统计 ===
        lines.append(f"\n  【摊牌统计】")
        lines.append(f"  摊牌次数:       {s['showdowns']}")
        if s['showdowns'] > 0:
            lines.append(f"  摊牌胜率:       {100*s['showdown_wins']/max(1,s['showdowns']):.1f}%")
        else:
            lines.append(f"  摊牌胜率:       N/A")
        lines.append(f"  摊牌失败:       {s['showdown_losses']}次")
        lines.append(f"  不摊牌胜:       {s['wins_without_showdown']}次")
        
        # === 底池统计 ===
        lines.append(f"\n  【底池统计】")
        lines.append(f"  赢得底池数:     {s['total_pots_won']}")
        lines.append(f"  平均赢得底池:   {s.get('avg_pot_won', 0):.0f}筹码")
        lines.append(f"  最大赢得底池:   {s['largest_pot_won']}筹码")
        
        # === 其他统计 ===
        lines.append(f"\n  【其他统计】")
        lines.append(f"  总弃牌:         {s['folds']}次")
        lines.append(f"  总跟注:         {s['call_count']}次")
        if s.get('eliminated'):
            lines.append(f"  游戏结果:       淘汰 (第{s['eliminated_at']}手)")
        elif s.get('victory'):
            lines.append(f"  游戏结果:       胜出 (第{s['victory_at']}手)")
        else:
            lines.append(f"  游戏结果:       未结束")
        
        # 对手分析
        lines.append(f"\n  【对手分析】")
        lines.append(f"  {self.shark_ai.get_opponent_summary()}")
        
        lines.append(f"\n{'='*60}\n")
        
        # 输出到文件或控制台
        report_text = '\n'.join(lines)
        
        if output_file:
            # 确保目录存在
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"  报告已保存到: {output_file}")
        else:
            print(report_text)


def run_multiple_benchmarks(num_tests: int = 3, max_hands_per_test: int = 10000, 
                           output_dir: str = "benchmark_results"):
    """
    运行多次测试取平均
    每轮测试直到鲨鱼AI被淘汰或胜出
    
    Args:
        num_tests: 测试轮数
        max_hands_per_test: 每轮最大手牌数（防止无限循环）
        output_dir: 报告输出目录
    """
    import os
    import datetime
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 创建带时间戳的子目录
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    result_dir = os.path.join(output_dir, f"shark_benchmark_{timestamp}")
    os.makedirs(result_dir, exist_ok=True)
    
    print(f"\n{'#'*60}")
    print(f"#  鲨鱼AI强度测试 - {num_tests}轮 (直到淘汰或胜出)")
    print(f"#  盲注: 10/20 (每1000手翻倍)")
    print(f"#  每轮上限: {max_hands_per_test}手")
    print(f"#  报告目录: {result_dir}")
    print(f"{'#'*60}\n")
    
    all_results = []
    victories = 0
    eliminations = 0
    
    for test_num in range(1, num_tests + 1):
        print(f"\n{'#'*60}")
        print(f"#  第 {test_num}/{num_tests} 轮测试")
        print(f"{'#'*60}")
        
        runner = SilentGameRunner(max_hands=max_hands_per_test)
        result = runner.run_benchmark()
        
        # 保存本轮报告到文件
        report_file = os.path.join(result_dir, f"shark_report_{test_num:03d}.txt")
        runner.print_report(output_file=report_file)
        
        all_results.append(result)
        
        # 统计胜率和淘汰率
        if result.get('victory'):
            victories += 1
        if result.get('eliminated'):
            eliminations += 1
    
    # 汇总
    print(f"\n{'#'*60}")
    print(f"#  汇总报告 ({num_tests}轮测试)")
    print(f"{'#'*60}\n")
    
    avg_hands = sum(r['hands_played'] for r in all_results) / num_tests
    avg_profit = sum(r['profit'] for r in all_results) / num_tests
    avg_wins = sum(r['hands_won'] for r in all_results) / num_tests
    avg_vpip = sum(r.get('vpip', 0) for r in all_results) / num_tests
    avg_pfr = sum(r.get('pfr', 0) for r in all_results) / num_tests
    avg_3bet = sum(r.get('three_bet_pct', 0) for r in all_results) / num_tests
    avg_cbet = sum(r.get('cbet_pct', 0) for r in all_results) / num_tests
    avg_fold_to_3bet = sum(r.get('fold_to_3bet_pct', 0) for r in all_results) / num_tests
    
    avg_rank = sum(r['final_rank'] for r in all_results) / num_tests
    
    # 构建汇总报告
    summary_lines = []
    summary_lines.append(f"\n{'#'*60}")
    summary_lines.append(f"#  鲨鱼AI汇总报告 ({num_tests}轮测试)")
    summary_lines.append(f"#  测试时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary_lines.append(f"{'#'*60}\n")
    
    summary_lines.append(f"  测试模式:       直到淘汰或胜出 (盲注10/20，每1000手翻倍)")
    summary_lines.append(f"  胜出次数:       {victories}/{num_tests} ({100*victories/num_tests:.1f}%)")
    summary_lines.append(f"  淘汰次数:       {eliminations}/{num_tests} ({100*eliminations/num_tests:.1f}%)")
    summary_lines.append(f"  平均手牌数:     {avg_hands:.1f}")
    summary_lines.append(f"  平均盈亏:       {avg_profit:+.0f}")
    summary_lines.append(f"  平均胜场:       {avg_wins:.1f}")
    summary_lines.append(f"  平均VPIP:       {avg_vpip:.1f}%")
    summary_lines.append(f"  平均PFR:        {avg_pfr:.1f}%")
    summary_lines.append(f"  平均3Bet:       {avg_3bet:.1f}%")
    summary_lines.append(f"  平均CBet:       {avg_cbet:.1f}%")
    summary_lines.append(f"  平均Fold to 3Bet: {avg_fold_to_3bet:.1f}%")
    summary_lines.append(f"  平均排名:       {avg_rank:.1f}/6")
    
    # 评估
    summary_lines.append(f"\n  --- 评估 ---")
    victory_rate = victories / num_tests
    if victory_rate >= 0.5:
        summary_lines.append(f"  [强] 鲨鱼AI胜率{victory_rate*100:.0f}%，表现优秀！")
    elif victory_rate >= 0.3:
        summary_lines.append(f"  [良] 鲨鱼AI胜率{victory_rate*100:.0f}%，表现尚可")
    elif victory_rate >= 0.1:
        summary_lines.append(f"  [中] 鲨鱼AI胜率{victory_rate*100:.0f}%，需要调整")
    else:
        summary_lines.append(f"  [弱] 鲨鱼AI胜率{victory_rate*100:.0f}%，需要大幅改进")
    
    summary_lines.append(f"\n{'#'*60}\n")
    
    summary_text = '\n'.join(summary_lines)
    
    # 打印到控制台
    print(summary_text)
    
    # 保存汇总报告
    summary_file = os.path.join(result_dir, "shark_report_summary.txt")
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary_text)
    print(f"  汇总报告已保存到: {summary_file}")
    print(f"  所有报告目录: {result_dir}")
    
    return all_results, result_dir


if __name__ == '__main__':
    # 运行100轮测试，每轮直到淘汰或胜出（盲注10/20固定）
    results, report_dir = run_multiple_benchmarks(num_tests=100, max_hands_per_test=10000)
