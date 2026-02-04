"""
对手数据追踪器
用于AI学习对手风格
"""

from typing import Dict, List
from texas_holdem.core.player import Player


class OpponentTracker:
    """追踪对手行为数据，用于AI分析"""
    
    def __init__(self):
        self.data: Dict[str, Dict] = {}
    
    def initialize(self, players: List[Player]):
        """初始化追踪数据"""
        self.data = {}
        for player in players:
            if not player.is_ai:  # 只追踪人类玩家
                self.data[player.name] = {
                    'hands_observed': 0,
                    'vpip': 0.0,
                    'pfr': 0.0,
                    'af': 0.0,
                    'hands_played': 0,
                    'preflop_actions': 0,
                    'preflop_raises': 0,
                    'voluntary_put': 0,
                    'total_hands': 0,
                    'folds': 0,
                    'calls': 0,
                    'raises': 0,
                    'bets': 0,
                }
    
    def update(self, player_name: str, action: str, street: str, amount: int = 0):
        """更新对手数据"""
        if player_name not in self.data:
            return
        
        stats = self.data[player_name]
        
        # 记录行动
        if action == 'fold':
            stats['folds'] += 1
        elif action == 'call':
            stats['calls'] += 1
        elif action == 'raise':
            stats['raises'] += 1
        elif action == 'bet':
            stats['bets'] += 1
        
        # 翻牌前统计
        if street == 'preflop':
            stats['total_hands'] += 1
            
            if action != 'fold':
                stats['hands_played'] += 1
                stats['voluntary_put'] += 1
            
            stats['preflop_actions'] += 1
            if action == 'raise':
                stats['preflop_raises'] += 1
        
        # 计算指标
        self._calculate_metrics(player_name)
    
    def _calculate_metrics(self, player_name: str):
        """计算关键指标"""
        stats = self.data[player_name]
        
        # VPIP
        if stats['total_hands'] >= 10:
            stats['vpip'] = stats['hands_played'] / stats['total_hands']
        
        # PFR
        if stats['preflop_actions'] > 0:
            stats['pfr'] = stats['preflop_raises'] / stats['preflop_actions']
        
        # AF (简化版)
        aggressive = stats['raises'] + stats['bets']
        passive = stats['calls']
        if passive > 0:
            stats['af'] = aggressive / passive
        else:
            stats['af'] = aggressive
    
    def get_style_analysis(self, player_name: str) -> Dict[str, str]:
        """获取玩家风格分析"""
        if player_name not in self.data:
            return {'style': 'unknown', 'description': '数据不足'}
        
        stats = self.data[player_name]
        vpip = stats.get('vpip', 0)
        pfr = stats.get('pfr', 0)
        af = stats.get('af', 0)
        
        # 判断松紧
        if vpip < 0.20:
            tightness = '紧'
        elif vpip < 0.30:
            tightness = '偏紧'
        elif vpip < 0.40:
            tightness = '偏松'
        else:
            tightness = '松'
        
        # 判断激进程度
        if af > 2.0 or (vpip > 0 and pfr / vpip > 0.6):
            aggression = '凶'
        elif af > 1.0:
            aggression = '偏凶'
        else:
            aggression = '弱'
        
        # 组合风格
        style = tightness + aggression
        
        return {
            'style': style,
            'vpip': f"{vpip*100:.1f}%",
            'pfr': f"{pfr*100:.1f}%",
            'af': f"{af:.2f}",
            'hands': str(stats['total_hands'])
        }
    
    def get_all_analysis(self) -> Dict[str, Dict]:
        """获取所有对手的分析"""
        return {name: self.get_style_analysis(name) for name in self.data.keys()}
