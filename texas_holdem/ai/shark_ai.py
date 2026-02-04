"""
鲨鱼AI - 自适应学习对手风格的AI
"""

import random
from typing import Dict, List, Tuple, Any
from texas_holdem.core.player import Player
from texas_holdem.game.betting import BettingRound
from texas_holdem.utils.constants import GameState


class SharkAI:
    """
    鲨鱼AI - 自适应学习AI
    
    特点：
    1. 初始使用GTO平衡策略
    2. 观察对手行为（20手后激活学习）
    3. 每轮根据对手数据动态调整策略
    4. 对手容易弃牌就多诈唬，对手喜欢诈唬就打更紧
    """
    
    def __init__(self):
        # 初始使用紧弱(LAP)风格，学习后动态调整
        self.base_config = {
            'vpip_range': (15, 22),      # 紧 - 只玩好牌
            'pfr_range': (5, 12),        # 弱 - 少加注多跟注
            'af_factor': 1.0,            # 低攻击性
            'bluff_freq': 0.05,          # 很少诈唬
            'call_preflop': 0.40,        # 喜欢跟注
            'raise_preflop': 0.10,       # 很少加注
            'bet_postflop': 0.20,        # 翻牌后下注少
            'fold_to_raise': 0.50,       # 容易被加注吓跑
            'adaptation_start': 20,
            'learning_rate': 0.1,
        }
        
        # 对手追踪数据
        self.opponent_data: Dict[str, Dict] = {}
        self.adaptation_active = False
        self.hands_observed = 0
        self.current_config = self.base_config.copy()
    
    def initialize_opponents(self, players: List[Player]):
        """初始化对手追踪"""
        self.opponent_data = {}
        for player in players:
            if not player.is_ai or player.ai_style != 'SHARK':
                self.opponent_data[player.name] = {
                    'hands_observed': 0,
                    'folds': 0,
                    'calls': 0,
                    'raises': 0,
                    'bluffs_detected': 0,
                    'bluff_opportunities': 0,
                    'fold_to_cbet': 0,
                    'cbet_opportunities': 0,
                    'showdown_wins': 0,
                    'showdowns': 0,
                    # 倾向值（0-1）
                    'fold_tendency': 0.5,
                    'bluff_tendency': 0.5,
                    'calling_tendency': 0.5,
                }
        self.adaptation_active = False
        self.hands_observed = 0
        self.current_config = self.base_config.copy()
    
    def update_after_action(self, player_name: str, action: str, street: str,
                           is_bluff: bool = False, facing_cbet: bool = False):
        """
        每轮行动后更新对手数据
        
        这是关键方法，确保每轮都能追踪对手行为
        """
        if player_name not in self.opponent_data:
            return
        
        data = self.opponent_data[player_name]
        data['hands_observed'] += 1
        self.hands_observed += 1
        
        # 记录行动
        if action == 'fold':
            data['folds'] += 1
            if facing_cbet:
                data['fold_to_cbet'] += 1
        elif action in ['call']:
            data['calls'] += 1
        elif action in ['raise', 'bet']:
            data['raises'] += 1
            if is_bluff:
                data['bluffs_detected'] += 1
        
        if facing_cbet:
            data['cbet_opportunities'] += 1
        
        # 检查是否达到激活学习的条件
        if not self.adaptation_active:
            total_hands = sum(d['hands_observed'] for d in self.opponent_data.values())
            if total_hands >= self.base_config['adaptation_start']:
                self.adaptation_active = True
                print("\n[🦈 鲨鱼AI] 已收集足够数据，开始自适应调整策略...")
        
        # 每5手更新一次倾向值（确保及时更新）
        if data['hands_observed'] % 5 == 0 or self.adaptation_active:
            self._calculate_tendencies(player_name)
            # 每次更新后都重新计算策略
            if self.adaptation_active:
                self._update_strategy()
    
    def _calculate_tendencies(self, player_name: str):
        """计算对手的倾向值"""
        data = self.opponent_data[player_name]
        hands = data['hands_observed']
        
        if hands < 3:
            return
        
        # 弃牌倾向
        fold_rate = data['folds'] / hands
        data['fold_tendency'] = min(1.0, max(0.0, fold_rate * 2))
        
        # 诈唬倾向
        if data['raises'] > 0:
            bluff_rate = data['bluffs_detected'] / data['raises']
            data['bluff_tendency'] = min(1.0, bluff_rate * 3)
        
        # 跟注倾向
        if hands > data['folds']:
            calling_rate = data['calls'] / (hands - data['folds'])
            data['calling_tendency'] = min(1.0, max(0.0, calling_rate))
    
    def _update_strategy(self):
        """根据对手数据更新当前策略配置"""
        if not self.opponent_data:
            return
        
        # 计算所有对手的平均倾向
        avg_fold = sum(d['fold_tendency'] for d in self.opponent_data.values()) / len(self.opponent_data)
        avg_bluff = sum(d['bluff_tendency'] for d in self.opponent_data.values()) / len(self.opponent_data)
        avg_call = sum(d['calling_tendency'] for d in self.opponent_data.values()) / len(self.opponent_data)
        
        # 基于倾向调整策略
        adjustments = []
        
        # 对手容易弃牌 -> 增加诈唬，减少入池
        if avg_fold > 0.6:
            self.current_config['bluff_freq'] = min(0.5, self.base_config['bluff_freq'] + 0.15)
            self.current_config['bet_postflop'] = min(0.7, self.base_config['bet_postflop'] + 0.15)
            self.current_config['af_factor'] = self.base_config['af_factor'] + 0.5
            adjustments.append("对手易弃牌→增加诈唬")
        
        # 对手喜欢诈唬 -> 打得更紧，增加抓诈
        if avg_bluff > 0.4:
            self.current_config['vpip_range'] = (
                max(15, self.base_config['vpip_range'][0] - 5),
                max(20, self.base_config['vpip_range'][1] - 5)
            )
            self.current_config['call_preflop'] = min(0.4, self.base_config['call_preflop'] + 0.1)
            self.current_config['fold_to_raise'] = max(0.3, self.base_config['fold_to_raise'] - 0.1)
            adjustments.append("对手爱诈唬→收紧范围")
        
        # 对手是跟注站 -> 减少诈唬，增加价值下注
        if avg_call > 0.5:
            self.current_config['bluff_freq'] = max(0.1, self.base_config['bluff_freq'] - 0.1)
            self.current_config['bet_postflop'] = self.base_config['bet_postflop'] + 0.1
            self.current_config['af_factor'] = self.base_config['af_factor'] + 0.3
            adjustments.append("对手跟注多→减少诈唬")
        
        # 如果没有任何调整，恢复基础配置
        if not adjustments:
            self.current_config = self.base_config.copy()
        
        return adjustments
    
    def get_action(self, player: Player, betting_round: BettingRound,
                   hand_strength: float, win_probability: float,
                   pot_odds: float, ev: float) -> Tuple[Any, int]:
        """
        鲨鱼AI决策
        """
        from texas_holdem.utils.constants import Action
        
        game_state = betting_round.game_state
        available_actions = betting_round.get_available_actions(player)
        amount_to_call = betting_round.get_amount_to_call(player)
        current_bet = game_state.current_bet
        
        config = self.current_config
        is_preflop = (game_state.state == GameState.PRE_FLOP)
        
        # 翻牌前紧弱起手牌选择（ tighter than before ）
        if is_preflop:
            if hand_strength < 0.58:  # 提高门槛，只玩更好的牌
                # 如果可以免费看牌，优先check
                if amount_to_call <= 0:
                    return Action.CHECK, 0
                if player.is_big_blind and amount_to_call <= 10:
                    return Action.CALL, 0
                return Action.FOLD, 0
            # 中等牌力（0.58-0.68）根据位置谨慎游戏
            elif hand_strength < 0.68:
                is_late = player.is_dealer or player.is_small_blind
                # 早位放弃，晚位才玩
                if not is_late:
                    if amount_to_call <= 0:
                        return Action.CHECK, 0
                    return Action.FOLD, 0
        
        # 根据手牌强度和当前配置选择行动
        action_weights = self._calculate_shark_weights(hand_strength, config)
        
        # 过滤可用行动
        available_names = [str(a).lower().replace('action.', '') for a in available_actions]
        valid = {k: v for k, v in action_weights.items() if k in available_names and v > 0}
        
        if not valid:
            return Action.FOLD, 0
        
        # 加权选择
        action_name = self._weighted_choice(valid)
        
        # 映射到Action
        action_map = {
            'fold': Action.FOLD,
            'check': Action.CHECK,
            'call': Action.CALL,
            'bet': Action.BET,
            'raise': Action.RAISE,
            'all_in': Action.ALL_IN
        }
        action = action_map.get(action_name, Action.FOLD)
        
        # 计算金额
        amount = self._calculate_shark_amount(
            action, player, amount_to_call, current_bet, hand_strength, config
        )
        
        return action, amount
    
    def _calculate_shark_weights(self, hand_strength: float, config: Dict) -> Dict[str, float]:
        """计算鲨鱼AI的行动权重 - 紧弱(LAP)风格"""
        weights = {'fold': 0, 'check': 0, 'call': 0, 'bet': 0, 'raise': 0, 'all_in': 0}
        
        # 紧弱调整
        adjusted = hand_strength - 0.05  # 更保守
        
        bluff_freq = config['bluff_freq']  # 低诈唬频率 (0.05)
        af = config['af_factor']  # 低攻击性 (1.0)
        
        if adjusted > 0.75:  # 超强牌
            # 即使强牌也更喜欢跟注而不是加注
            weights.update({
                'call': 0.45,
                'bet': 0.30,
                'raise': 0.25,
            })
        elif adjusted > 0.55:  # 强牌
            # 被动地跟注，少加注
            weights.update({
                'call': 0.50,
                'bet': 0.25,
                'raise': 0.15,
                'fold': 0.10,
            })
        elif adjusted > 0.40:  # 中等牌
            # 更多地跟注看牌，少下注
            weights.update({
                'call': 0.55,
                'check': 0.20,
                'fold': 0.15,
                'bet': 0.08,
                'raise': 0.02,
            })
        elif adjusted > 0.30:  # 中等偏弱
            # 紧弱风格：能弃就弃，能check就check，很少诈唬
            weights.update({
                'fold': 0.40,
                'check': 0.35,
                'call': 0.22,
                'bet': 0.02 * bluff_freq * 10,  # 极少诈唬
                'raise': 0.01 * bluff_freq * 10
            })
        else:  # 弱牌
            # 紧弱：弃牌或check，基本不诈唬
            weights.update({
                'fold': 0.60,
                'check': 0.30,
                'call': 0.09,
                'bet': 0.01 * bluff_freq * 10  # 几乎不诈唬
            })
        
        return weights
    
    def _calculate_shark_amount(self, action, player, amount_to_call, current_bet,
                                hand_strength, config) -> int:
        """计算鲨鱼AI的下注金额"""
        if action == 'fold' or action == 'check':
            return 0
        elif action == 'call':
            return 0
        elif action == 'all_in':
            return player.chips
        
        big_blind = 20
        af = config['af_factor']
        
        if current_bet == 0:  # bet
            if hand_strength > 0.75:
                return big_blind * int(3 + af * 0.5)
            elif hand_strength > 0.55:
                return big_blind * int(2.5 + af * 0.3)
            else:
                return big_blind * 2
        else:  # raise
            min_raise = max(big_blind * 2, current_bet)
            if hand_strength > 0.75:
                return min_raise + big_blind * int(2 + af * 0.3)
            elif hand_strength > 0.55:
                return min_raise + big_blind * int(1 + af * 0.2)
            else:
                return min_raise
    
    def _weighted_choice(self, weights: Dict[str, float]) -> str:
        """加权随机选择"""
        total = sum(weights.values())
        if total == 0:
            return 'fold'
        
        r = random.random() * total
        cumulative = 0
        for action, weight in weights.items():
            cumulative += weight
            if r <= cumulative:
                return action
        return list(weights.keys())[-1]
    
    def get_opponent_summary(self) -> str:
        """获取对手分析摘要"""
        if not self.adaptation_active:
            return "[🦈 鲨鱼AI] 观察中..."
        
        summaries = []
        for name, data in self.opponent_data.items():
            if data['hands_observed'] >= 5:
                fold_desc = "易弃牌" if data['fold_tendency'] > 0.6 else \
                           "难弃牌" if data['fold_tendency'] < 0.4 else "中等"
                bluff_desc = "爱诈唬" if data['bluff_tendency'] > 0.4 else \
                            "诚实" if data['bluff_tendency'] < 0.2 else "平衡"
                summaries.append(f"{name}({fold_desc}/{bluff_desc})")
        
        if summaries:
            return f"[🦈 鲨鱼AI] 分析: {', '.join(summaries)}"
        return "[🦈 鲨鱼AI] 学习中..."
