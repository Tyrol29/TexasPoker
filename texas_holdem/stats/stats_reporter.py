"""
统计报告生成器
生成详细的玩家统计报告
"""

from typing import Dict, Any, List


class StatsReporter:
    """统计报告生成器"""
    
    def __init__(self):
        self.style_names = {
            'TAG': '紧凶',
            'LAG': '松凶',
            'LAP': '紧弱',
            'LP': '松弱',
            'SHARK': '鲨鱼'
        }
        
        self.style_descriptions = {
            'TAG': '紧凶 (Tight Aggressive) - 精选手牌，积极加注',
            'LAG': '松凶 (Loose Aggressive) - 多玩手牌，持续施压',
            'LAP': '紧弱 (Tight Passive) - 精选手牌，跟注为主',
            'LP': '松弱 (Loose Passive) - 多玩手牌，被动跟注',
            'SHARK': '鲨鱼 (Adaptive AI) - 初始GTO打法，自适应调整'
        }
    
    def generate_report(self, player_stats: Dict, total_hands: int,
                       player_styles: Dict) -> str:
        """
        生成统计报告
        
        Returns:
            报告字符串
        """
        lines = []
        lines.append(f"\n{'='*100}")
        lines.append(f"[统计报告] 玩家打法分析 (前{total_hands}手牌)")
        lines.append(f"{'='*100}")
        
        for name, stats in player_stats.items():
            if stats.get('hands_played', 0) == 0:
                continue
            
            report = self._generate_player_report(name, stats, player_styles)
            lines.extend(report)
        
        lines.append(f"\n{'='*100}")
        lines.append("指标说明:")
        lines.append("  VPIP = 主动入池率 | PFR = 翻牌前加注率 | 3BET = 再加注频率 | AF = 激进因子")
        lines.append("  WTSD = 摊牌率 | W$SD = 摊牌胜率 | 不摊牌胜 = 对手弃牌赢得的底池")
        lines.append("  弃3BET = 面对再加注的弃牌率 | 偷盲率 = 后位抢盲频率 | C-BET = 持续下注率")
        lines.append(f"{'='*100}")
        
        return '\n'.join(lines)
    
    def _generate_player_report(self, name: str, stats: Dict, 
                                player_styles: Dict) -> List[str]:
        """生成单个玩家的报告"""
        lines = []
        
        # 获取风格
        style = player_styles.get(name, 'TAG')
        style_cn = self.style_names.get(style, style)
        
        # 基础数据
        hands = stats.get('hands_played', 0)
        
        # 计算百分比
        vpip_pct = (stats.get('vpip', 0) / hands * 100) if hands > 0 else 0
        pfr_pct = (stats.get('pfr', 0) / hands * 100) if hands > 0 else 0
        three_bet_pct = (stats.get('three_bet', 0) / hands * 100) if hands > 0 else 0
        
        # AF计算
        aggressive = stats.get('af', {}).get('bet', 0) + stats.get('af', {}).get('raise', 0)
        passive = stats.get('af', {}).get('call', 0)
        af = aggressive / passive if passive > 0 else aggressive
        
        # 风格判断
        actual_style = self._classify_style(vpip_pct, pfr_pct, af)
        
        # 第一行：基础指标
        lines.append(f"\n{name:<15} | VPIP:{vpip_pct:5.1f}% | PFR:{pfr_pct:5.1f}% | "
                    f"3BET:{three_bet_pct:4.1f}% | AF:{af:.2f} | "
                    f"预设:{style_cn:<6} | 实际:{actual_style}")
        lines.append("  " + "-"*96)
        
        # 高级指标
        wtsd_pct, wsd_pct, wws_pct = self._calculate_advanced_stats(stats, hands)
        fold_3bet_pct = self._calculate_fold_3bet(stats)
        
        lines.append(f"  摊牌率WTSD:{wtsd_pct:4.1f}% | 摊牌胜率W$SD:{wsd_pct:4.1f}% | "
                    f"不摊牌胜:{wws_pct:4.1f}% | 弃3BET:{fold_3bet_pct:4.1f}% | "
                    f"ALL-IN:{stats.get('all_ins', 0)}次")
        
        # 其他指标
        steal_pct, cbet_pct, bluff_pct = self._calculate_other_stats(stats)
        avg_bet = self._calculate_avg_bet(stats)
        
        lines.append(f"  偷盲率:{steal_pct:4.1f}% | C-BET率:{cbet_pct:4.1f}% | "
                    f"诈唬成功率:{bluff_pct:4.1f}% | 均注:{avg_bet:5.0f} | "
                    f"总弃牌:{stats.get('folds', 0)}次")
        
        # 街道统计
        flop_vpip = stats.get('street_vpip', {}).get('flop', 0)
        turn_vpip = stats.get('street_vpip', {}).get('turn', 0)
        river_vpip = stats.get('street_vpip', {}).get('river', 0)
        
        lines.append(f"  街道入池: 翻牌FLOP:{flop_vpip:3d} | 转牌TURN:{turn_vpip:3d} | "
                    f"河牌RIVER:{river_vpip:3d}")
        
        # 最大盈亏
        lines.append(f"  最大赢池:{stats.get('biggest_win', 0):6d} | "
                    f"最大损失:{stats.get('biggest_loss', 0):6d} | "
                    f"摊牌次数:{stats.get('showdowns', 0):3d}/{hands:3d}")
        
        return lines
    
    def _classify_style(self, vpip: float, pfr: float, af: float) -> str:
        """根据数据判断实际风格"""
        is_tight = vpip < 25
        is_aggressive = af > 2.0 or (vpip > 0 and pfr / vpip > 0.5)
        
        if is_tight and is_aggressive:
            return 'TAG(紧凶)'
        elif not is_tight and is_aggressive:
            return 'LAG(松凶)'
        elif is_tight and not is_aggressive:
            return 'LAP(紧弱)'
        else:
            return 'LP(松弱)'
    
    def _calculate_advanced_stats(self, stats: Dict, hands: int) -> tuple:
        """计算高级指标"""
        # WTSD
        wtsd_pct = (stats.get('showdowns', 0) / hands * 100) if hands > 0 else 0
        
        # W$SD
        showdowns = stats.get('showdowns', 0)
        wsd_pct = (stats.get('showdown_wins', 0) / showdowns * 100) if showdowns > 0 else 0
        
        # 不摊牌胜率
        non_showdown = hands - showdowns
        wws_pct = (stats.get('wins_without_showdown', 0) / non_showdown * 100) \
                  if non_showdown > 0 else 0
        
        return wtsd_pct, wsd_pct, wws_pct
    
    def _calculate_fold_3bet(self, stats: Dict) -> float:
        """计算弃3BET率"""
        face_3bet = stats.get('face_3bet', 0)
        if face_3bet == 0:
            return 0.0
        return stats.get('fold_to_3bet', 0) / face_3bet * 100
    
    def _calculate_other_stats(self, stats: Dict) -> tuple:
        """计算其他指标"""
        # 偷盲率
        steal_ops = stats.get('steal_opportunities', 0)
        steal_pct = (stats.get('steal_attempts', 0) / steal_ops * 100) \
                    if steal_ops > 0 else 0
        
        # C-BET率
        cbet_ops = stats.get('cbet_opportunities', 0)
        cbet_pct = (stats.get('cbet_made', 0) / cbet_ops * 100) \
                   if cbet_ops > 0 else 0
        
        # 诈唬成功率
        bluffs = stats.get('bluffs_attempted', 0)
        bluff_pct = (stats.get('bluffs_successful', 0) / bluffs * 100) \
                    if bluffs > 0 else 0
        
        return steal_pct, cbet_pct, bluff_pct
    
    def _calculate_avg_bet(self, stats: Dict) -> float:
        """计算平均下注额"""
        bets = stats.get('af', {}).get('bet', 0)
        raises = stats.get('af', {}).get('raise', 0)
        total = bets + raises
        
        if total == 0:
            return 0
        
        return stats.get('total_bet_amount', 0) / total
    
    def get_style_description(self, style: str) -> str:
        """获取风格描述"""
        return self.style_descriptions.get(style, '未知风格')
