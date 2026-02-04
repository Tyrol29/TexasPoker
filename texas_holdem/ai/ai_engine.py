"""
AI引擎 - 管理各种AI风格的决策逻辑
"""

import random
from typing import Dict, Tuple, List, Any
from texas_holdem.core.player import Player
from texas_holdem.game.betting import BettingRound
from texas_holdem.utils.constants import GameState


class AIEngine:
    """AI决策引擎"""
    
    def __init__(self):
        # 打法风格参数配置
        self.style_configs = {
            'TAG': {  # 紧凶 - Tight Aggressive
                'vpip_range': (15, 25),
                'pfr_range': (12, 20),
                'af_factor': 2.5,
                'bluff_freq': 0.15,
                'call_preflop': 0.20,
                'raise_preflop': 0.25,
                'bet_postflop': 0.40,
                'fold_to_raise': 0.60,
            },
            'LAG': {  # 松凶 - Loose Aggressive
                'vpip_range': (30, 45),
                'pfr_range': (20, 30),
                'af_factor': 2.0,
                'bluff_freq': 0.25,
                'call_preflop': 0.35,
                'raise_preflop': 0.30,
                'bet_postflop': 0.50,
                'fold_to_raise': 0.40,
            },
            'LAP': {  # 紧弱 - Tight Passive
                'vpip_range': (15, 22),
                'pfr_range': (5, 12),
                'af_factor': 1.0,
                'bluff_freq': 0.05,
                'call_preflop': 0.40,
                'raise_preflop': 0.10,
                'bet_postflop': 0.20,
                'fold_to_raise': 0.50,
            },
            'LP': {  # 松弱 - Loose Passive
                'vpip_range': (35, 50),
                'pfr_range': (8, 15),
                'af_factor': 0.8,
                'bluff_freq': 0.08,
                'call_preflop': 0.50,
                'raise_preflop': 0.12,
                'bet_postflop': 0.25,
                'fold_to_raise': 0.30,
            },
        }
    
    def get_action(self, player: Player, betting_round: BettingRound,
                   hand_strength: float, win_probability: float,
                   pot_odds: float, ev: float) -> Tuple[Any, int]:
        """
        获取AI行动
        
        Returns:
            (action, amount) 元组
        """
        from texas_holdem.utils.constants import Action
        
        game_state = betting_round.game_state
        available_actions = betting_round.get_available_actions(player)
        amount_to_call = betting_round.get_amount_to_call(player)
        current_bet = game_state.current_bet
        
        style = getattr(player, 'ai_style', 'LAG')
        
        # 如果是鲨鱼，需要特殊处理
        if style == 'SHARK':
            # 鲨鱼AI使用自己的决策方法
            return self._shark_decision(player, betting_round, hand_strength,
                                        win_probability, pot_odds, ev)
        
        config = self.style_configs.get(style, self.style_configs['LAG'])
        
        return self._choose_action_by_style(
            player, available_actions, amount_to_call, current_bet,
            hand_strength, game_state.state, config, pot_odds, win_probability, ev
        )
    
    def _shark_decision(self, player, betting_round, hand_strength,
                       win_probability, pot_odds, ev):
        """鲨鱼AI决策（由SharkAI类处理）"""
        # 这里会被SharkAI类覆盖
        from texas_holdem.utils.constants import Action
        return Action.FOLD, 0
    
    def _choose_action_by_style(self, player, available_actions, amount_to_call,
                                current_bet, hand_strength, game_state, config,
                                pot_odds, win_probability, ev) -> Tuple[Any, int]:
        """根据风格选择行动"""
        from texas_holdem.utils.constants import Action
        
        is_preflop = (game_state == GameState.PRE_FLOP)
        style = getattr(player, 'ai_style', 'LAG')
        
        # 翻牌前起手牌选择
        if is_preflop:
            threshold = self._get_preflop_threshold(style)
            if hand_strength < threshold:
                if player.is_big_blind and amount_to_call <= 10:
                    return (Action.CALL if amount_to_call > 0 else Action.CHECK, 0)
                return Action.FOLD, 0
        
        # 根据手牌强度选择行动权重
        action_weights = self._calculate_action_weights(
            hand_strength, style, config
        )
        
        # 根据可用行动过滤
        available_names = [str(a).lower().replace('action.', '') for a in available_actions]
        
        # 选择行动
        action_name = self._weighted_choice(action_weights, available_names)
        
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
        amount = self._calculate_amount(
            action, player, amount_to_call, current_bet, 
            hand_strength, config
        )
        
        return action, amount
    
    def _get_preflop_threshold(self, style: str) -> float:
        """获取翻牌前起手牌阈值"""
        thresholds = {
            'TAG': 0.58,
            'LAG': 0.35,
            'LAP': 0.58,
            'LP': 0.35,
        }
        return thresholds.get(style, 0.40)
    
    def _calculate_action_weights(self, hand_strength: float, style: str, 
                                  config: Dict) -> Dict[str, float]:
        """计算行动权重"""
        weights = {'fold': 0, 'check': 0, 'call': 0, 'bet': 0, 'raise': 0, 'all_in': 0}
        
        # 根据风格调整
        tightness = {
            'TAG': 0.10, 'LAG': -0.05, 'LAP': 0.08, 'LP': -0.08
        }.get(style, 0)
        
        adjusted = hand_strength - tightness
        
        if adjusted > 0.75:  # 超强牌
            if style in ['TAG', 'LAG']:
                weights.update({'raise': 0.55, 'bet': 0.30, 'call': 0.15})
            elif style == 'LAP':
                weights.update({'raise': 0.15, 'bet': 0.25, 'call': 0.50, 'check': 0.10})
            else:
                weights.update({'raise': 0.30, 'bet': 0.40, 'call': 0.30})
        elif adjusted > 0.55:  # 强牌
            if style in ['TAG', 'LAG']:
                weights.update({'raise': 0.40, 'bet': 0.35, 'call': 0.25})
            elif style == 'LAP':
                weights.update({'raise': 0.10, 'bet': 0.20, 'call': 0.60, 'fold': 0.10})
            else:
                weights.update({'raise': 0.15, 'bet': 0.30, 'call': 0.55})
        elif adjusted > 0.40:  # 中等牌
            if style == 'TAG':
                weights.update({'fold': 0.20, 'raise': 0.15, 'bet': 0.25, 'call': 0.40})
            elif style == 'LAG':
                weights.update({'raise': 0.25, 'bet': 0.30, 'call': 0.35, 'fold': 0.10})
            elif style == 'LAP':
                weights.update({'call': 0.70, 'fold': 0.20, 'bet': 0.05, 'raise': 0.05})
            else:
                weights.update({'call': 0.65, 'fold': 0.15, 'bet': 0.15, 'raise': 0.05})
        else:  # 弱牌
            if style in ['TAG', 'LAP']:
                weights.update({'fold': 0.70, 'check': 0.20, 'call': 0.10})
            else:
                weights.update({'fold': 0.40, 'check': 0.30, 'call': 0.20, 'bet': 0.10})
        
        return weights
    
    def _weighted_choice(self, weights: Dict[str, float], available: List[str]) -> str:
        """加权随机选择"""
        # 过滤可用行动
        valid = {k: v for k, v in weights.items() if k in available and v > 0}
        
        if not valid:
            return 'fold' if 'fold' in available else available[0] if available else 'fold'
        
        total = sum(valid.values())
        r = random.random() * total
        
        cumulative = 0
        for action, weight in valid.items():
            cumulative += weight
            if r <= cumulative:
                return action
        
        return list(valid.keys())[-1]
    
    def _calculate_amount(self, action, player, amount_to_call, current_bet,
                         hand_strength, config) -> int:
        """计算下注金额"""
        if action == 'fold' or action == 'check':
            return 0
        elif action == 'call':
            return 0  # 由游戏引擎处理
        elif action == 'all_in':
            return player.chips
        
        # bet 或 raise
        big_blind = 20  # 默认大盲
        
        if current_bet == 0:  # bet
            if hand_strength > 0.75:
                return big_blind * 4
            elif hand_strength > 0.55:
                return big_blind * 3
            else:
                return big_blind * 2
        else:  # raise
            min_raise = max(big_blind * 2, current_bet)
            if hand_strength > 0.75:
                return min_raise + big_blind * 2
            elif hand_strength > 0.55:
                return min_raise + big_blind
            else:
                return min_raise
    
    # 手牌评估方法
    @staticmethod
    def evaluate_hand_strength(hole_cards, community_cards) -> float:
        """评估手牌强度（0.0-1.0）"""
        from texas_holdem.core.evaluator import PokerEvaluator
        
        if not hole_cards:
            return 0.5
        
        all_cards = hole_cards + community_cards
        
        if len(all_cards) >= 5:
            rank, values = PokerEvaluator.evaluate_hand(all_cards)
            base_strength = rank / 9.0
            
            if values:
                high_card_bonus = values[0] / 14.0 * 0.2
                return min(1.0, base_strength + high_card_bonus)
            return base_strength
        else:
            return AIEngine._evaluate_preflop_strength(hole_cards)
    
    @staticmethod
    def _evaluate_preflop_strength(hole_cards) -> float:
        """翻牌前手牌强度评估"""
        if len(hole_cards) != 2:
            return 0.5
        
        card1, card2 = hole_cards
        val1, val2 = card1.value, card2.value
        
        # 对子
        if val1 == val2:
            pair_strength = val1 / 14.0
            return 0.6 + pair_strength * 0.3
        
        # 同花
        suited = card1.suit == card2.suit
        
        # 连牌
        gap = abs(val1 - val2)
        connected = gap <= 2
        
        # 高牌
        high_card = max(val1, val2)
        high_strength = high_card / 14.0
        
        base = 0.3
        if suited:
            base += 0.1
        if connected:
            base += 0.1
        base += high_strength * 0.2
        
        return min(0.7, base)
    
    @staticmethod
    def calculate_pot_odds(total_pot, amount_to_call) -> float:
        """计算底池赔率"""
        if amount_to_call <= 0:
            return 0
        if total_pot == 0:
            return float('inf')
        return amount_to_call / total_pot
    
    @staticmethod
    def estimate_win_probability(hole_cards, community_cards) -> float:
        """估算胜率（简化版蒙特卡洛）"""
        return AIEngine.evaluate_hand_strength(hole_cards, community_cards)
    
    @staticmethod
    def calculate_expected_value(hand_strength, pot_odds, amount_to_call, total_pot) -> float:
        """计算期望值"""
        if pot_odds == 0:
            return 0.1
        
        win_prob = hand_strength * 0.8 + 0.1
        pot_ratio = 1 / (pot_odds + 1) if pot_odds != float('inf') else 0
        
        ev = win_prob * total_pot - (1 - win_prob) * amount_to_call
        return ev
