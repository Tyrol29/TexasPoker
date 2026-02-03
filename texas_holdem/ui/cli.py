"""
命令行界面
提供德州扑克游戏的命令行交互
"""

import sys
import time
import random
import itertools
from typing import List, Optional, Dict, Tuple
from texas_holdem.core.player import Player
from texas_holdem.core.table import Table
from texas_holdem.core.evaluator import PokerEvaluator
from texas_holdem.core.card import Card
from texas_holdem.game.game_engine import GameEngine
from texas_holdem.game.betting import BettingRound
from texas_holdem.utils.constants import Action, GameState, SMALL_BLIND, BIG_BLIND, INITIAL_CHIPS

class CLI:
    """命令行界面类"""

    def __init__(self):
        self.game_engine = None
        self.player_names = []
        self.opponent_stats = {}  # 对手统计数据
        self.hand_history = []    # 手牌历史记录
        
        # 详细的玩家统计跟踪（用于100手报告）
        self.player_stats = {}    # {player_name: {stat_name: value}}
        self.current_hand_actions = {}  # 当前手牌各玩家的行动
        self.total_hands = 0      # 总局数
        self.stats_report_interval = 100  # 每100手输出报告
        
        # 玩家打法风格 {player_name: 'TAG'/'LAG'/'LAP'/'LP'}
        self.player_styles = {}
        
        # 缓存电脑行动，在玩家行动前批量输出
        self.pending_actions = []  # [(player_name, action_desc, stage), ...]
        self.current_stage_name = "翻牌前"
        
        # 盲注升级跟踪
        self.initial_ai_count = 0      # 初始电脑数量
        self.blind_level = 1           # 盲注级别
        self.blind_doubled = False     # 是否已翻倍
        
        # 打法风格参数配置
        self.style_configs = {
            'TAG': {  # 紧凶 - Tight Aggressive
                'vpip_range': (15, 25),      # 入池率
                'pfr_range': (12, 20),       # 加注率
                'af_factor': 2.5,             # 激进因子
                'bluff_freq': 0.15,           # 诈唬频率
                'call_preflop': 0.20,         # 翻牌前跟注倾向
                'raise_preflop': 0.25,        # 翻牌前加注倾向
                'bet_postflop': 0.40,         # 翻牌后下注倾向
                'fold_to_raise': 0.60,        # 面对加注弃牌率
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
            }
        }

    def display_welcome(self):
        """显示欢迎信息"""
        print("=" * 60)
        print("          德州扑克两人对战游戏")
        print("=" * 60)
        print("\n规则:")
        print("  • 两人对战德州扑克")
        print(f"  • 初始筹码: {INITIAL_CHIPS}")
        print(f"  • 小盲注: {SMALL_BLIND}, 大盲注: {BIG_BLIND}")
        print("  • 游戏包含四个下注轮次: 翻牌前、翻牌、转牌、河牌")
        print("  • 支持行动: 弃牌、过牌、跟注、下注、加注、全押")
        print("\n" + "=" * 60)

    def get_player_names(self) -> List[str]:
        """获取玩家名称 - 支持2-8人游戏"""
        names = []
        print("\n" + "="*50)
        print("游戏设置")
        print("="*50)
        
        # 选择总玩家人数
        while True:
            try:
                total_players = input("\n请选择玩家人数 (2-8, 默认6): ").strip()
                if not total_players:
                    total_players = 6
                else:
                    total_players = int(total_players)
                if 2 <= total_players <= 8:
                    break
                else:
                    print("请输入2-8之间的数字")
            except ValueError:
                print("请输入有效数字")
        
        # 选择AI数量
        max_ai = total_players - 1  # 至少留1个位置给人类玩家
        while True:
            try:
                ai_count = input(f"\n请选择AI玩家数量 (1-{max_ai}, 默认{max_ai}): ").strip()
                if not ai_count:
                    ai_count = max_ai
                else:
                    ai_count = int(ai_count)
                if 1 <= ai_count <= max_ai:
                    break
                else:
                    print(f"请输入1-{max_ai}之间的数字")
            except ValueError:
                print("请输入有效数字")
        
        human_count = total_players - ai_count
        
        print(f"\n游戏配置: 共{total_players}人 (AI×{ai_count}, 人类×{human_count})")
        print("-"*50)
        
        # 添加AI玩家（随机分配风格）
        reserved_names = set()
        available_styles = ['TAG', 'LAG', 'LAP', 'LP']
        style_names = {'TAG': '紧凶', 'LAG': '松凶', 'LAP': '紧弱', 'LP': '松弱'}
        
        for i in range(1, ai_count + 1):
            style = random.choice(available_styles)
            style_cn = style_names[style]
            ai_name = f"电脑{i}号[{style_cn}]"
            names.append(ai_name)
            reserved_names.add(ai_name)
            print(f"玩家{i}: {ai_name} (AI-{style_cn})")
        
        # 添加人类玩家
        for i in range(1, human_count + 1):
            player_num = ai_count + i
            while True:
                name = input(f"\n请输入玩家{player_num}的名称: ").strip()
                if not name:
                    print("名称不能为空")
                elif name in reserved_names:
                    print("该名称已被使用，请使用其他名称")
                else:
                    names.append(name)
                    reserved_names.add(name)
                    print(f"玩家{player_num}: {name} (人类)")
                    break
        
        return names

    def _get_position_name(self, player, players, game_state):
        """
        获取玩家在德州扑克中的标准位置名称
        
        位置顺序（从D开始逆时针）：
        - D: 庄家 (Dealer)
        - SB: 小盲 (Small Blind)
        - BB: 大盲 (Big Blind)
        - UTG: 枪口位 (Under The Gun) - BB后第一个
        - UTG+1: 枪口位+1
        - MP: 中间位置 (Middle Position)
        - CO:  cutoff位 (Cutoff) - D前第二个
        - BTN: 按钮位 (同D)
        """
        num_players = len(players)
        
        # 找到玩家索引
        player_idx = players.index(player)
        
        # 找到庄家索引
        dealer_idx = -1
        for i, p in enumerate(players):
            if p.is_dealer:
                dealer_idx = i
                break
        
        if dealer_idx == -1:
            return ""
        
        # 计算相对位置（距离庄家的位置）
        # 位置编号：D=0, SB=1, BB=2, UTG=3, ...
        relative_pos = (player_idx - dealer_idx) % num_players
        
        # 标准位置映射
        if relative_pos == 0:
            return "BTN"
        elif relative_pos == 1:
            return "SB"
        elif relative_pos == 2:
            return "BB"
        elif relative_pos == num_players - 1:  # D前一个
            return "CO"
        elif relative_pos == num_players - 2 and num_players >= 4:  # D前两个
            return "HJ"
        elif relative_pos == 3:
            return "UTG"
        elif relative_pos == 4 and num_players >= 6:
            return "UTG+1"
        elif relative_pos == 5 and num_players >= 7:
            return "MP"
        elif relative_pos == 6 and num_players >= 8:
            return "MP+1"
        else:
            return "MP"

    def display_table(self, game_state, show_all_hands=False, pending_actions=None):
        """显示牌桌状态 - 简洁版，带标准位置标记"""
        table = game_state.table
        players = game_state.players
        
        # 阶段名称映射
        stage_names = {
            GameState.PRE_FLOP: "🂠 翻牌前",
            GameState.FLOP: "🂡 翻牌圈",
            GameState.TURN: "🂢 转牌圈", 
            GameState.RIVER: "🂣 河牌圈",
            GameState.SHOWDOWN: "[摊牌]"
        }
        stage = stage_names.get(game_state.state, game_state.state)
        
        print(f"\n【{stage}】 底池: 💰{table.total_pot}")
        
        # 显示公共牌
        community_cards = table.get_community_cards()
        if community_cards:
            print(f"公共牌: {' '.join(str(card) for card in community_cards)}")
        
        # 显示玩家信息（一行一个，带位置标记）
        for player in players:
            # 获取标准位置名称
            pos_name = self._get_position_name(player, players, game_state)
            
            # 状态标记
            status_marks = []
            if not player.is_active:
                status_marks.append("✕")
            if player.is_all_in:
                status_marks.append("ALL")
            
            status_str = f"[{','.join(status_marks)}]" if status_marks else ""
            
            # 组合位置和状态标记
            if status_str:
                mark_str = f"[{pos_name}{status_str}]"
            else:
                mark_str = f"[{pos_name}]"
            
            # 手牌显示（仅人类玩家、摊牌阶段或show_all_hands）
            hand_str = ""
            if player.hand.get_cards():
                if (player.is_active and not player.is_ai) or game_state.state == GameState.SHOWDOWN or show_all_hands:
                    hand_str = f" {player.hand}"
                else:
                    hand_str = " 🂠🂠"
            
            # 当前下注
            bet_str = f" 注:{player.bet_amount}" if player.bet_amount > 0 else ""
            
            # 如果有待显示的操作记录
            action_str = ""
            if pending_actions and player.name in pending_actions:
                action_str = f" ← {pending_actions[player.name]}"
            
            print(f"  {mark_str:8} {player.name:10} {player.chips:5}筹码{bet_str:8}{hand_str}{action_str}")
        
        print("-" * 55)

    def get_player_action(self, player: Player, betting_round: BettingRound) -> tuple:
        """
        获取玩家行动输入

        Args:
            player: 当前玩家
            betting_round: 下注轮次对象

        Returns:
            (行动, 金额) 元组
        """
        # 如果是AI玩家，使用AI策略
        if player.is_ai:
            return self.get_ai_action(player, betting_round)

        # 人类玩家：先输出缓存的电脑行动，再显示信息并获取输入
        self._flush_pending_actions()
        
        available_actions = betting_round.get_available_actions(player)
        amount_to_call = betting_round.get_amount_to_call(player)
        
        # 显示底池总额（包含当前轮次所有玩家的下注）
        # 计算主池 + 当前轮次所有玩家已下注的金额
        current_bets_sum = sum(p.bet_amount for p in betting_round.game_state.players)
        total_pot = betting_round.game_state.table.total_pot + current_bets_sum
        print(f"\n{'='*40}")
        print(f"底池总额: {total_pot} 筹码")
        print(f"{'='*40}")

        print(f"\n{player.name} 的回合")
        print(f"手牌: {player.hand}")
        print(f"筹码: {player.chips}")
        print(f"当前下注额: {betting_round.game_state.current_bet}")
        if amount_to_call > 0:
            print(f"需要跟注: {amount_to_call}")

        print(f"\n可用行动: {', '.join(available_actions)}")

        while True:
            action_input = input("请选择行动: ").strip().lower()

            if not action_input:
                print("请输入行动")
                continue

            # 解析行动
            parts = action_input.split()
            action = parts[0]

            # 处理缩写
            action_map = {
                'f': Action.FOLD,
                'c': Action.CALL if amount_to_call > 0 else Action.CHECK,
                'k': Action.CHECK,
                'b': Action.BET,
                'r': Action.RAISE,
                'a': Action.ALL_IN,
                'fold': Action.FOLD,
                'check': Action.CHECK,
                'call': Action.CALL,
                'bet': Action.BET,
                'raise': Action.RAISE,
                'allin': Action.ALL_IN,
                'all_in': Action.ALL_IN
            }

            if action not in action_map:
                print(f"无效行动: {action}")
                print(f"可用行动: {', '.join(available_actions)}")
                continue

            action = action_map[action]

            # 检查行动是否可用
            if action not in available_actions:
                print(f"行动 '{action}' 当前不可用")
                continue

            # 处理需要金额的行动
            amount = 0
            if action in [Action.BET, Action.RAISE]:
                if len(parts) < 2:
                    print(f"请指定{action}金额")
                    continue

                try:
                    amount = int(parts[1])
                    if amount <= 0:
                        print("金额必须大于0")
                        continue
                except ValueError:
                    print("金额必须是数字")
                    continue

            # 验证行动
            is_valid, error_msg = betting_round.validate_action(player, action, amount)
            if not is_valid:
                print(f"行动无效: {error_msg}")
                continue

            return action, amount

    def display_action_result(self, message: str):
        """显示行动结果"""
        print(f"> {message}")

    def display_hand_result(self, winners: List[Player], winnings: dict):
        """显示手牌结果"""
        if not winners:
            return

        print("\n" + "=" * 60)
        print("手牌结果:")
        print("=" * 60)

        if len(winners) == 1:
            print(f"\n*** {winners[0].name} 获胜! ***")
        else:
            print(f"\n🤝 平局! 赢家: {', '.join(w.name for w in winners)}")

        for player, amount in winnings.items():
            print(f"{player.name} 赢得 {amount} 筹码")

        print("=" * 60)

    def run_interactive_game(self):
        """运行交互式游戏 - 支持2-8人"""
        self.display_welcome()
        self.player_names = self.get_player_names()

        # 创建游戏引擎
        self.game_engine = GameEngine(self.player_names, INITIAL_CHIPS)

        # 自动识别AI玩家（名称以"电脑"开头）并提取风格
        ai_count = 0
        human_count = 0
        
        # 风格名称映射（中文->英文）
        style_map = {'紧凶': 'TAG', '松凶': 'LAG', '紧弱': 'LAP', '松弱': 'LP'}
        
        for player in self.game_engine.players:
            if player.name.startswith("电脑"):
                player.is_ai = True
                ai_count += 1
                
                # 从名称中提取风格（例如"电脑1号[紧凶]"）
                style = 'LAG'  # 默认风格
                if '[' in player.name and ']' in player.name:
                    cn_style = player.name.split('[')[1].split(']')[0]
                    style = style_map.get(cn_style, 'LAG')
                
                player.ai_style = style
                self.player_styles[player.name] = style
            else:
                human_count += 1

        # 初始化对手统计数据
        self._initialize_opponent_stats(self.game_engine.players)
        
        # 初始化玩家详细统计
        self._initialize_player_stats()
        
        # 记录初始电脑数量（用于盲注升级）
        self.initial_ai_count = ai_count
        self.blind_level = 1
        self.blind_doubled = False

        game_state = self.game_engine.game_state

        print(f"\n{'='*50}")
        print("游戏开始!")
        print(f"{'='*50}")
        print(f"\n玩家人数: {len(self.player_names)}人 (AI×{ai_count}, 人类×{human_count})")
        print(f"初始筹码: {INITIAL_CHIPS}")
        print(f"初始盲注: 小盲{SMALL_BLIND}, 大盲{BIG_BLIND}")
        print(f"盲注规则: 第一个电脑被淘汰后，盲注翻倍！")
        
        # 显示各电脑玩家的打法风格说明
        print(f"\n[打法风格说明]")
        style_descriptions = {
            'TAG': '紧凶 (Tight Aggressive) - 精选手牌，积极加注',
            'LAG': '松凶 (Loose Aggressive) - 多玩手牌，持续施压',
            'LAP': '紧弱 (Tight Passive) - 精选手牌，跟注为主',
            'LP': '松弱 (Loose Passive) - 多玩手牌，被动跟注'
        }
        for player in self.game_engine.players:
            if player.is_ai:
                style = player.ai_style
                print(f"  {player.name}: {style_descriptions.get(style, style)}")
        print(f"{'='*50}")

        hand_number = 0

        while True:  # 无限游戏，直到有玩家出局
            hand_number += 1
            self.total_hands += 1  # 修复：移到开始处，确保每手都计数
            
            print(f"\n{'='*50}")
            print(f"第 {hand_number} 手牌")
            print(f"{'='*50}")

            # 开始新的一手牌
            self.game_engine.start_new_hand()
            
            # 清空上一手牌的行动缓存
            self._clear_pending_actions()
            self.current_stage_name = "翻牌前"
            
            # 更新每个玩家的手牌计数（只要参与了手牌就统计）
            for player in game_state.players:
                if player.name in self.player_stats:
                    self.player_stats[player.name]['hands_played'] += 1
            
            self.display_table(game_state)

            # 翻牌前下注
            if not self._run_betting_round_interactive():
                # 检查是否只剩一个玩家有筹码
                active_players = [p for p in game_state.players if p.chips > 0]
                if len(active_players) < 2:
                    break
                # 一手牌结束（有人赢得底池），跳到淘汰检查
                # 使用continue跳过剩余阶段，直接进入下一轮
                # 注意：不能直接用continue，需要执行淘汰检查
                # 通过设置标记来跳过剩余阶段
                hand_finished = True
            else:
                hand_finished = False
            
            if not hand_finished:
                # 发翻牌
                self.game_engine.deal_flop()
                game_state.advance_stage()
                self.current_stage_name = "翻牌圈"
                self.display_table(game_state)

                # 翻牌圈下注
                if not self._run_betting_round_interactive():
                    active_players = [p for p in game_state.players if p.chips > 0]
                    if len(active_players) < 2:
                        break
                    hand_finished = True
            
            if not hand_finished:
                # 发转牌
                self.game_engine.deal_turn()
                game_state.advance_stage()
                self.current_stage_name = "转牌圈"
                self.display_table(game_state)

                # 转牌圈下注
                if not self._run_betting_round_interactive():
                    active_players = [p for p in game_state.players if p.chips > 0]
                    if len(active_players) < 2:
                        break
                    hand_finished = True
            
            if not hand_finished:
                # 发河牌
                self.game_engine.deal_river()
                game_state.advance_stage()
                self.current_stage_name = "河牌圈"
                self.display_table(game_state)

                # 河牌圈下注
                if not self._run_betting_round_interactive():
                    active_players = [p for p in game_state.players if p.chips > 0]
                    if len(active_players) < 2:
                        break
                    # 一手牌结束
                else:
                    # 摊牌
                    self._run_showdown()
            
            # 检查并淘汰筹码归零的电脑玩家
            eliminated = self._eliminate_broke_players()
            if eliminated:
                print(f"\n{'='*50}")
                print("[淘汰通知]")
                for name, is_ai in eliminated:
                    player_type = "电脑" if is_ai else "玩家"
                    print(f"  {player_type} {name} 筹码归零，被淘汰！")
                print(f"{'='*50}")
                
                # 检查剩余玩家
                remaining_ai = len([p for p in game_state.players if p.is_ai])
                remaining_human = len([p for p in game_state.players if not p.is_ai])
                print(f"\n剩余玩家: 电脑×{remaining_ai}, 人类×{remaining_human}")
                
                # 检查是否是第一个电脑被淘汰，触发盲注翻倍
                eliminated_ai_count = sum(1 for _, is_ai in eliminated if is_ai)
                if eliminated_ai_count > 0 and not self.blind_doubled:
                    self._increase_blinds()
                
                # 如果只剩一个玩家，结束游戏
                if len(game_state.players) < 2:
                    print("\n*** 游戏结束：只剩一个玩家！***")
                    break
                
                # 如果没有电脑了，人类获胜
                if remaining_ai == 0 and remaining_human > 0:
                    print("\n*** 恭喜！所有电脑已被淘汰，人类获胜！***")
                    break
                
                # 如果没有人类了，电脑获胜
                if remaining_human == 0:
                    print("\n*** 很遗憾，所有人类玩家已被淘汰！***")
                    break
            
            # 每100手输出统计报告
            if self.total_hands % self.stats_report_interval == 0:
                print(f"\n{'='*50}")
                print(f"[系统] 已完成 {self.total_hands} 手牌，输出统计报告...")
                print(f"{'='*50}")
                self._print_stats_report()
                input("\n按回车键继续游戏...")

            # 检查游戏是否结束（需要至少2人有筹码）
            active_players = [p for p in game_state.players if p.chips > 0]
            if len(active_players) < 2:
                break

        # 显示最终结果
        print(f"\n{'='*50}")
        print(f"游戏结束! 共进行了 {hand_number} 手牌")
        # 游戏结束时输出最终统计
        if self.total_hands > 0:
            self._print_stats_report()
        self._display_final_results()

    def _run_betting_round_interactive(self) -> bool:
        """运行交互式下注轮次 - 实时显示所有玩家操作"""
        game_state = self.game_engine.game_state
        betting_round = self.game_engine.betting_round

        # 重置玩家行动状态
        game_state.reset_player_actions()
        
        # 跟踪本圈下注统计
        preflop_raiser = None  # 翻牌前加注者（用于C-bet统计）
        current_bet_level = 0  # 当前下注级别（用于检测3bet）
        players_acted = []  # 已行动玩家列表（用于偷盲检测）

        while not game_state.is_betting_round_complete():
            current_player = game_state.get_current_player()
            if not current_player:
                break

            # 获取玩家行动
            action, amount = self.get_player_action(current_player, betting_round)
            
            # 处理行动前检测特殊场景
            street_map = {
                GameState.PRE_FLOP: 'preflop',
                GameState.FLOP: 'flop',
                GameState.TURN: 'turn',
                GameState.RIVER: 'river'
            }
            street = street_map.get(game_state.state, 'unknown')
            action_str = str(action).lower().replace('action.', '')
            
            # 检测是否是偷盲位置（CO/BTN位置且前面都弃牌）
            is_steal_position = False
            if street == 'preflop' and current_player.is_ai:
                position = self._get_position_name(current_player, game_state.players, game_state)
                if position in ['CO', 'BTN', 'HJ'] and len(players_acted) > 0:
                    # 检查前面是否都弃牌了
                    all_folded = all(p_action == 'fold' for p_name, p_action in players_acted)
                    if all_folded:
                        is_steal_position = True
            
            # 检测是否是C-bet机会（翻牌前加注者在翻牌圈第一个行动）
            is_cbet_opportunity = False
            if street == 'flop' and preflop_raiser == current_player.name:
                # 翻牌前加注者，且在翻牌圈第一个行动
                is_cbet_opportunity = True
            
            # 检测是否面对3bet（当前需要跟注的金额 >= 60）
            amount_to_call = betting_round.get_amount_to_call(current_player)
            facing_3bet = (street == 'preflop' and amount_to_call >= 40 and current_bet_level >= 1)

            # 处理行动
            success, message, bet_amount = betting_round.process_action(
                current_player, action, amount
            )

            if success:
                # 记录行动
                players_acted.append((current_player.name, action_str))
                
                # 跟踪翻牌前加注者
                if street == 'preflop' and action_str == 'raise':
                    if current_bet_level == 0:
                        preflop_raiser = current_player.name
                    current_bet_level += 1
                
                # 格式化行动描述
                action_desc = self._format_action_message(action, amount)
                position_name = self._get_position_name(current_player, game_state.players, game_state)
                
                if current_player.is_ai:
                    # 电脑行动：缓存起来，等玩家行动前再输出
                    self.pending_actions.append((current_player.name, action_desc, self.current_stage_name, position_name))
                else:
                    # 人类玩家行动：立即输出
                    print(f"→ [{position_name}] {current_player.name}: {action_desc}")
                
                # 每次行动后更新牌桌显示（仅人类玩家或需要刷新时）
                if not current_player.is_ai:
                    self.display_table(game_state)

                # 更新对手统计数据（如果当前玩家是AI的对手）
                if not current_player.is_ai:
                    self._update_opponent_stats(current_player.name, action_str, street, amount)
                
                # 判断是否是诈唬（简化：河牌弱牌下注视为诈唬）
                is_bluff = (game_state.state == GameState.RIVER and 
                           action_str in ['bet', 'raise'] and 
                           self._evaluate_hand_strength(current_player.hand.get_cards(), 
                                                        game_state.table.get_community_cards()) < 0.4)
                
                # 判断是否是C-bet执行
                cbet_made = is_cbet_opportunity and action_str in ['bet', 'raise']
                
                # 判断是否是偷盲尝试
                steal_attempt = is_steal_position and action_str in ['raise', 'bet']
                
                # 更新详细统计（所有玩家）
                self._update_player_stats(
                    current_player.name, action_str, street, amount, is_bluff,
                    fold_to_3bet=facing_3bet, 
                    steal_opportunity=is_steal_position,
                    steal_attempt=steal_attempt,
                    cbet_opportunity=is_cbet_opportunity,
                    cbet_made=cbet_made
                )
            else:
                print(f"行动失败: {message}")
                continue

            # 移动到下一个玩家
            game_state.next_player()

            # 检查是否只剩一个活动玩家
            if game_state.get_active_player_count() <= 1:
                winner = game_state.get_active_players()[0]
                # 输出本阶段行动历史
                self._flush_pending_actions()
                print(f"\n*** {winner.name} 获胜! ***")
                side_pots = betting_round.collect_bets()
                # 计算赢家赢得的金额（简化：赢得整个底池）
                win_amount = game_state.table.total_pot
                winner.collect_winnings(win_amount)
                print(f"    赢得 {win_amount} 筹码")
                # 更新赢池统计
                if winner.name in self.player_stats:
                    if win_amount > self.player_stats[winner.name]['biggest_win']:
                        self.player_stats[winner.name]['biggest_win'] = win_amount
                    # 记录不摊牌获胜（其他人都弃牌了）
                    self.player_stats[winner.name]['wins_without_showdown'] += 1
                    # 清零赢家的投入
                    self.player_stats[winner.name]['current_hand_invested'] = 0
                # 其他玩家的投入已在行动中累计，这里更新损失并清零
                for player in game_state.players:
                    if player.name in self.player_stats and player != winner:
                        invested = self.player_stats[player.name]['current_hand_invested']
                        if invested > 0 and invested > self.player_stats[player.name]['biggest_loss']:
                            self.player_stats[player.name]['biggest_loss'] = invested
                        self.player_stats[player.name]['current_hand_invested'] = 0
                return False

        # 收集下注到底池
        side_pots = betting_round.collect_bets()
        return True
    
    def _format_action_message(self, action, amount):
        """格式化行动描述为简短形式"""
        action_names = {
            'fold': '弃牌',
            'check': '过牌',
            'call': '跟注',
            'bet': f'下注{amount}',
            'raise': f'加注{amount}',
            'all_in': '全押'
        }
        return action_names.get(action, action)

    def _flush_pending_actions(self):
        """输出缓存的电脑行动（在人类玩家行动前调用）"""
        if self.pending_actions:
            print(f"\n{'-'*40}")
            print(f"[本阶段行动记录]")
            for player_name, action_desc, stage, position in self.pending_actions:
                print(f"  [{position}] {player_name}: {action_desc}")
            print(f"{'-'*40}")
            self.pending_actions = []

    def _clear_pending_actions(self):
        """清空缓存的行动"""
        self.pending_actions = []

    def _show_all_actions(self):
        """在摊牌时显示本手牌所有行动历史"""
        if self.pending_actions:
            print(f"\n{'='*50}")
            print("[本手牌完整行动记录]")
            print(f"{'='*50}")
            current_stage = None
            for player_name, action_desc, stage, position in self.pending_actions:
                if stage != current_stage:
                    current_stage = stage
                    print(f"\n【{stage}】")
                print(f"  [{position}] {player_name}: {action_desc}")
            print(f"{'='*50}")
            self.pending_actions = []

    def _run_showdown(self):
        """运行摊牌 - 显示所有玩家手牌和行动历史"""
        game_state = self.game_engine.game_state
        game_state.advance_stage()
        
        # 确保输出所有缓存的行动
        self.current_stage_name = "摊牌"

        winners = self.game_engine.determine_showdown_winners()
        
        # 分配底池并获取赢家赢得的金额
        winnings = self.game_engine.award_pots(winners)
        
        # 更新最大赢池和损失统计
        self._update_win_loss_stats(winnings, game_state)

        # 输出本手牌所有行动历史
        self._show_all_actions()

        # 显示摊牌详情（所有玩家，包括弃牌的）
        print(f"\n{'='*50}")
        print("[摊牌] 所有玩家手牌")
        
        community_cards = game_state.table.get_community_cards()
        print(f"公共牌: {' '.join(str(card) for card in community_cards)}")
        print()

        # 显示所有玩家的手牌（不只是active的）
        for player in game_state.players:
            if player.hand.get_cards():
                all_cards = player.hand.get_cards() + community_cards
                hand_desc = PokerEvaluator.get_best_hand_description(all_cards)
                
                # 标记状态
                status = ""
                won = player in winners
                if won:
                    status = "[获胜]"
                elif not player.is_active:
                    status = "[弃牌]"
                elif player.is_all_in:
                    status = "[全押]"
                
                print(f"  {player.name:10} {player.hand} → {hand_desc} {status}")
                
                # 更新玩家摊牌统计
                if player.name in self.player_stats:
                    reached_sd = player.is_active or player.is_all_in
                    # hands_played 已经在手牌开始时更新，这里只更新摊牌相关统计
                    if reached_sd:
                        self.player_stats[player.name]['showdowns'] += 1
                        if won:
                            self.player_stats[player.name]['showdown_wins'] += 1
                    elif won:
                        # 没有摊牌但获胜（其他人都弃牌了）
                        self.player_stats[player.name]['wins_without_showdown'] += 1

        print(f"{'='*50}")

    def _update_win_loss_stats(self, winnings, game_state):
        """
        更新最大赢池和损失统计
        
        Args:
            winnings: {player: amount} 赢家赢得的金额字典
            game_state: 游戏状态
        """
        # 更新赢家统计
        for player, win_amount in winnings.items():
            if player.name in self.player_stats and win_amount > 0:
                # 更新最大赢池
                if win_amount > self.player_stats[player.name]['biggest_win']:
                    self.player_stats[player.name]['biggest_win'] = win_amount
        
        # 更新输家统计
        for player in game_state.players:
            if player.name in self.player_stats:
                won_amount = winnings.get(player, 0)
                invested = self.player_stats[player.name]['current_hand_invested']
                
                # 净损失 = 投入 - 赢得（如果投入大于赢得）
                if invested > won_amount:
                    loss = invested - won_amount
                    if loss > self.player_stats[player.name]['biggest_loss']:
                        self.player_stats[player.name]['biggest_loss'] = loss
                
                # 清零当前手牌投入，为下一手做准备
                self.player_stats[player.name]['current_hand_invested'] = 0

    def _display_final_results(self):
        """显示最终结果 - 简洁版"""
        print(f"\n{'='*50}")
        print("[最终排名]")
        print(f"{'='*50}")

        players = self.game_engine.players
        players_sorted = sorted(players, key=lambda p: p.chips, reverse=True)

        for i, player in enumerate(players_sorted, 1):
            status = "[存活]" if player.chips > 0 else "[淘汰]"
            print(f"  {i}. {player.name:10} {player.chips:6}筹码 {status}")

        winner = players_sorted[0]
        print(f"\n*** 恭喜 {winner.name} 获胜! ***")
        print(f"{'='*50}")

    def _initialize_player_stats(self):
        """初始化玩家详细统计"""
        self.player_stats = {}
        self.total_hands = 0
        for name in self.player_names:
            self.player_stats[name] = {
                'hands_played': 0,      # 参与的手牌数
                'vpip': 0,              # 主动入池次数(Voluntarily Put Money In Pot)
                'pfr': 0,               # 翻牌前加注次数(Pre-Flop Raise)
                'three_bet': 0,         # 3bet次数
                'four_bet': 0,          # 4bet次数
                'af': {'bet': 0, 'raise': 0, 'call': 0},  # 激进因子统计
                'showdowns': 0,         # 摊牌次数
                'showdown_wins': 0,     # 摊牌获胜次数
                'folds': 0,             # 弃牌次数
                'checks': 0,            # 过牌次数
                'total_actions': 0,     # 总行动次数
                'bluffs_attempted': 0,  # 尝试诈唬次数
                'bluffs_successful': 0, # 诈唬成功次数
                # 新增技术指标
                'wins_without_showdown': 0,  # 不摊牌获胜次数
                'fold_to_3bet': 0,      # 面对3bet弃牌次数
                'face_3bet': 0,         # 遭遇3bet次数
                'steal_attempts': 0,    # 偷盲尝试次数
                'steal_opportunities': 0, # 偷盲机会次数（后位+前面都弃牌）
                'cbet_opportunities': 0,  # C-bet机会（翻牌前加注且翻牌后第一个行动）
                'cbet_made': 0,         # C-bet实际执行次数
                'check_raise_opportunities': 0,  # Check-raise机会
                'check_raise_made': 0,  # Check-raise实际次数
                'all_ins': 0,           # All-in次数
                'total_bet_amount': 0,  # 总下注额
                'street_vpip': {'flop': 0, 'turn': 0, 'river': 0},  # 各街道入池
                'street_actions': {'flop': [], 'turn': [], 'river': []},  # 各街道行动记录
                'biggest_win': 0,       # 最大赢得底池
                'biggest_loss': 0,      # 最大损失
                'current_hand_invested': 0,  # 当前手牌已投入（临时字段，每手结束清零）
            }

    def _update_player_stats(self, player_name, action, street, amount=0, is_bluff=False, 
                              won_hand=False, reached_showdown=False, fold_to_3bet=False,
                              steal_opportunity=False, steal_attempt=False, 
                              cbet_opportunity=False, cbet_made=False):
        """更新玩家统计"""
        if player_name not in self.player_stats:
            return
        
        stats = self.player_stats[player_name]
        stats['total_actions'] += 1
        
        # 记录具体行动
        if action in ['bet']:
            stats['af']['bet'] += 1
        elif action in ['raise']:
            stats['af']['raise'] += 1
        elif action in ['call']:
            stats['af']['call'] += 1
        elif action in ['fold']:
            stats['folds'] += 1
        elif action in ['check']:
            stats['checks'] += 1
        elif action in ['all_in']:
            stats['all_ins'] += 1
        
        # VPIP: 翻牌前主动入池(加注/跟注/下注)
        if street == 'preflop' and action in ['raise', 'call', 'bet']:
            stats['vpip'] += 1
        
        # 各街道VPIP统计
        if street in ['flop', 'turn', 'river'] and action in ['bet', 'raise', 'call']:
            stats['street_vpip'][street] += 1
            stats['street_actions'][street].append(action)
        
        # PFR: 翻牌前加注
        if street == 'preflop' and action in ['raise']:
            stats['pfr'] += 1
        
        # 3bet/4bet检测(简化版)
        if street == 'preflop' and action in ['raise']:
            if amount >= 60:  # 3bet roughly
                stats['three_bet'] += 1
            if amount >= 120:  # 4bet roughly
                stats['four_bet'] += 1
        
        # 面对3bet弃牌统计
        if fold_to_3bet:
            stats['face_3bet'] += 1
            if action == 'fold':
                stats['fold_to_3bet'] += 1
        
        # 偷盲统计
        if steal_opportunity:
            stats['steal_opportunities'] += 1
        if steal_attempt:
            stats['steal_attempts'] += 1
        
        # C-bet统计
        if cbet_opportunity:
            stats['cbet_opportunities'] += 1
        if cbet_made:
            stats['cbet_made'] += 1
        
        # 总下注额和当前手牌投入
        if action in ['bet', 'raise', 'all_in', 'call'] and amount > 0:
            stats['total_bet_amount'] += amount
            stats['current_hand_invested'] += amount  # 累计当前手牌投入
        
        # 诈唬统计
        if is_bluff:
            stats['bluffs_attempted'] += 1
            if won_hand:
                stats['bluffs_successful'] += 1
        
        # 摊牌统计
        if reached_showdown:
            stats['showdowns'] += 1
            if won_hand:
                stats['showdown_wins'] += 1
        elif won_hand:
            # 不摊牌获胜
            stats['wins_without_showdown'] += 1

    def _print_stats_report(self):
        """输出详细玩家统计报告 - 包含多项技术指标"""
        print(f"\n{'='*100}")
        print(f"[统计报告] 玩家打法分析 (前{self.total_hands}手牌)")
        print(f"{'='*100}")
        
        # 风格中文名称
        style_names = {
            'TAG': '紧凶',
            'LAG': '松凶',
            'LAP': '紧弱',
            'LP': '松弱'
        }
        
        for name, stats in self.player_stats.items():
            if stats['hands_played'] == 0:
                continue
            
            hands = self.total_hands
            vpip_pct = (stats['vpip'] / hands * 100) if hands > 0 else 0
            pfr_pct = (stats['pfr'] / hands * 100) if hands > 0 else 0
            three_bet_pct = (stats['three_bet'] / hands * 100) if hands > 0 else 0
            
            # AF = (下注+加注) / 跟注
            aggressive = stats['af']['bet'] + stats['af']['raise']
            passive = stats['af']['call']
            af = aggressive / passive if passive > 0 else aggressive
            
            # 获取预设风格和实际风格
            preset_style = self.player_styles.get(name, '-')
            preset_short = style_names.get(preset_style, preset_style)
            actual_style_full = self._classify_player_style(vpip_pct, pfr_pct, af)
            # 提取风格代码（如"TAG(紧凶)" -> "TAG"）
            actual_style_code = actual_style_full.split('(')[0] if '(' in actual_style_full else actual_style_full
            actual_short = style_names.get(actual_style_code, actual_style_code)
            
            # 分析偏离详情
            deviation_analysis = self._analyze_style_deviation(preset_style, vpip_pct, pfr_pct, af)
            
            # 判断是否符合预设
            if preset_style == '-' or preset_style == actual_style_code:
                diff = "符合" if preset_style != '-' else "人类"
            else:
                diff = "偏离"
            
            display_name = name[:14]
            
            # === 基础指标行 ===
            print(f"\n{display_name:<15} | VPIP:{vpip_pct:5.1f}% | PFR:{pfr_pct:5.1f}% | 3BET:{three_bet_pct:4.1f}% | "
                  f"AF:{af:4.2f} | 预设:{preset_short:<6} | 实际:{actual_style_full:<10} [{diff}]")
            
            # 显示偏离分析
            if deviation_analysis:
                print(f"  [偏离分析] {deviation_analysis}")
            
            # === 高级指标行1 ===
            # WTSD% (摊牌率)
            wtsd_pct = (stats['showdowns'] / stats['hands_played'] * 100) if stats['hands_played'] > 0 else 0
            # W$SD% (摊牌胜率)
            wsd_pct = (stats['showdown_wins'] / stats['showdowns'] * 100) if stats['showdowns'] > 0 else 0
            # 不摊牌胜率
            wws_pct = (stats['wins_without_showdown'] / (stats['hands_played'] - stats['showdowns']) * 100) \
                      if (stats['hands_played'] - stats['showdowns']) > 0 else 0
            # Fold to 3Bet%
            fold_3bet_pct = (stats['fold_to_3bet'] / stats['face_3bet'] * 100) if stats['face_3bet'] > 0 else 0
            
            print(f"  {'─'*95}")
            print(f"  摊牌率WTSD:{wtsd_pct:4.1f}% | 摊牌胜率W$SD:{wsd_pct:4.1f}% | 不摊牌胜:{wws_pct:4.1f}% | "
                  f"弃3BET:{fold_3bet_pct:4.1f}% | ALL-IN:{stats['all_ins']}次")
            
            # === 高级指标行2 ===
            # 偷盲率
            steal_pct = (stats['steal_attempts'] / stats['steal_opportunities'] * 100) \
                        if stats['steal_opportunities'] > 0 else 0
            # C-bet率
            cbet_pct = (stats['cbet_made'] / stats['cbet_opportunities'] * 100) \
                       if stats['cbet_opportunities'] > 0 else 0
            # 诈唬成功率
            bluff_pct = (stats['bluffs_successful'] / stats['bluffs_attempted'] * 100) \
                        if stats['bluffs_attempted'] > 0 else 0
            # 平均下注额
            avg_bet = stats['total_bet_amount'] / (stats['af']['bet'] + stats['af']['raise']) \
                      if (stats['af']['bet'] + stats['af']['raise']) > 0 else 0
            
            print(f"  偷盲率:{steal_pct:4.1f}% | C-BET率:{cbet_pct:4.1f}% | 诈唬成功率:{bluff_pct:4.1f}% | "
                  f"均注:{avg_bet:5.0f} | 总弃牌:{stats['folds']}次")
            
            # === 各街道统计 ===
            flop_vpip = stats['street_vpip']['flop']
            turn_vpip = stats['street_vpip']['turn']
            river_vpip = stats['street_vpip']['river']
            print(f"  街道入池: 翻牌FLOP:{flop_vpip:3d} | 转牌TURN:{turn_vpip:3d} | 河牌RIVER:{river_vpip:3d}")
            
            # 最大盈亏
            print(f"  最大赢池:{stats['biggest_win']:6d} | 最大损失:{stats['biggest_loss']:6d} | "
                  f"摊牌次数:{stats['showdowns']:3d}/{stats['hands_played']:3d}")
        
        print(f"\n{'='*100}")
        print("指标说明:")
        print("  VPIP = 主动入池率 | PFR = 翻牌前加注率 | 3BET = 再加注频率 | AF = 激进因子(下注+加注)/跟注")
        print("  WTSD = 摊牌率(看对手牌的频率) | W$SD = 摊牌胜率 | 不摊牌胜 = 对手弃牌赢得的底池")
        print("  弃3BET = 面对再加注的弃牌率 | 偷盲率 = 后位抢盲频率 | C-BET = 持续下注率(翻牌前加注者在翻牌圈下注)")
        print("  紧凶(TAG): VPIP<25%, AF>2 | 松凶(LAG): VPIP>30%, AF>2 | 紧弱(LAP): VPIP<25%, AF<1.5 | 松弱(LP): VPIP>35%, AF<1.5")
        print(f"{'='*100}")

    def _eliminate_broke_players(self):
        """
        淘汰筹码归零的玩家
        
        Returns:
            被淘汰的玩家列表 [(name, is_ai), ...]
        """
        eliminated = []
        remaining_players = []
        remaining_stats = {}
        
        game_state = self.game_engine.game_state
        
        for player in game_state.players:
            if player.chips <= 0:
                # 记录被淘汰的玩家
                eliminated.append((player.name, player.is_ai))
                print(f"  [淘汰] {player.name} ({'电脑' if player.is_ai else '人类'}) 筹码归零")
            else:
                remaining_players.append(player)
                # 保留统计信息
                if player.name in self.player_stats:
                    remaining_stats[player.name] = self.player_stats[player.name]
        
        if eliminated:
            # 更新游戏引擎中的玩家列表
            self.game_engine.players = remaining_players
            game_state.players = remaining_players
            game_state.active_players = [p for p in remaining_players if p.is_active]
            
            # 更新统计信息字典
            self.player_stats = remaining_stats
            
            # 更新风格字典（移除被淘汰玩家）
            for name, _ in eliminated:
                if name in self.player_styles:
                    del self.player_styles[name]
            
            # 更新玩家名称列表
            self.player_names = [p.name for p in remaining_players]
            
        return eliminated

    def _increase_blinds(self):
        """增加盲注（翻倍）- 锦标赛模式"""
        import texas_holdem.utils.constants as constants
        
        # 获取当前盲注值
        old_sb = constants.SMALL_BLIND
        old_bb = constants.BIG_BLIND
        
        # 盲注翻倍
        new_sb = old_sb * 2
        new_bb = old_bb * 2
        
        # 更新模块级别的常量
        constants.SMALL_BLIND = new_sb
        constants.BIG_BLIND = new_bb
        
        self.blind_level += 1
        self.blind_doubled = True
        
        print(f"\n{'='*60}")
        print("[盲注升级]")
        print(f"{'='*60}")
        print(f"  第 {self.blind_level} 级别")
        print(f"  小盲注: {old_sb} → {new_sb}")
        print(f"  大盲注: {old_bb} → {new_bb}")
        print(f"  第一个电脑已被淘汰，盲注翻倍！")
        print(f"{'='*60}")

    def _classify_player_style(self, vpip, pfr, af):
        """根据统计判断玩家风格"""
        # TAG: Tight-Aggressive (紧凶)
        # LAG: Loose-Aggressive (松凶)
        # LAP: Tight-Passive (紧弱)
        # LP: Loose-Passive (松弱)
        
        is_tight = vpip < 25  # 紧
        is_aggressive = af > 2.0 or (pfr / vpip > 0.5 if vpip > 0 else False)
        
        if is_tight and is_aggressive:
            return "TAG(紧凶)"
        elif is_tight and not is_aggressive:
            return "LAP(紧弱)"
        elif not is_tight and is_aggressive:
            return "LAG(松凶)"
        else:
            return "LP(松弱)"
    
    def _analyze_style_deviation(self, preset_style, vpip, pfr, af):
        """
        分析玩家打法偏离预设风格的具体细节
        
        Returns:
            偏离描述字符串，如果没有偏离则返回空字符串
        """
        if preset_style == '-' or not preset_style:
            return ""
        
        deviations = []
        
        # 定义各风格的目标范围
        style_targets = {
            'TAG': {'vpip': (15, 25), 'af': (2.0, 4.0)},      # 紧凶
            'LAG': {'vpip': (30, 45), 'af': (2.0, 4.0)},      # 松凶
            'LAP': {'vpip': (15, 25), 'af': (0.5, 1.5)},      # 紧弱
            'LP':  {'vpip': (35, 50), 'af': (0.5, 1.5)},      # 松弱
        }
        
        if preset_style not in style_targets:
            return ""
        
        targets = style_targets[preset_style]
        
        # 分析松紧度 (VPIP)
        if vpip < targets['vpip'][0]:
            deviations.append(f"偏紧(VPIP{vpip:.1f}% < 目标{targets['vpip'][0]}%)")
        elif vpip > targets['vpip'][1]:
            deviations.append(f"偏松(VPIP{vpip:.1f}% > 目标{targets['vpip'][1]}%)")
        
        # 分析凶弱度 (AF)
        if af < targets['af'][0]:
            deviations.append(f"偏弱(AF{af:.2f} < 目标{targets['af'][0]})")
        elif af > targets['af'][1]:
            deviations.append(f"偏凶(AF{af:.2f} > 目标{targets['af'][1]})")
        
        # 分析PFR/VPIP比例（攻击倾向）
        if vpip > 0:
            pfr_vpip_ratio = pfr / vpip
            if pfr_vpip_ratio < 0.4:
                deviations.append(f"跟注过多(PFR/VPIP{pfr_vpip_ratio:.2f}偏低)")
            elif pfr_vpip_ratio > 0.8:
                deviations.append(f"加注过多(PFR/VPIP{pfr_vpip_ratio:.2f}偏高)")
        
        if deviations:
            return "; ".join(deviations)
        return ""

    def run_auto_game(self, hands: int = 5):
        """运行自动游戏（用于测试）"""
        print("\n运行自动游戏（测试模式）...")

        # 使用默认玩家名称
        self.player_names = ["玩家1", "玩家2"]
        self.game_engine = GameEngine(self.player_names, INITIAL_CHIPS)

        print(f"玩家: {', '.join(self.player_names)}")
        print(f"运行 {hands} 手牌...\n")

        self.game_engine.run(hands)

    def main_menu(self):
        """显示主菜单"""
        while True:
            print("\n" + "=" * 60)
            print("德州扑克主菜单")
            print("=" * 60)
            print("1. 开始新游戏 (交互模式)")
            print("2. 运行测试游戏 (自动模式)")
            print("3. 游戏规则说明")
            print("4. 退出")
            print("=" * 60)

            choice = input("请选择 (1-4): ").strip()

            if choice == '1':
                self.run_interactive_game()
            elif choice == '2':
                try:
                    hands = int(input("运行几手牌? (默认 5): ").strip() or "5")
                    self.run_auto_game(hands)
                except ValueError:
                    print("请输入有效数字")
            elif choice == '3':
                self.display_rules()
            elif choice == '4':
                print("谢谢游玩!")
                break
            else:
                print("无效选择，请重试")

    def get_ai_action(self, player: Player, betting_round: BettingRound) -> tuple:
        """
        AI玩家决策

        Args:
            player: AI玩家
            betting_round: 下注轮次对象

        Returns:
            (行动, 金额) 元组
        """
        import random
        from texas_holdem.core.evaluator import PokerEvaluator

        game_state = betting_round.game_state
        available_actions = betting_round.get_available_actions(player)
        amount_to_call = betting_round.get_amount_to_call(player)
        current_bet = game_state.current_bet

        # AI决策（简洁显示）
        community_cards = game_state.table.get_community_cards()
        hand_strength = self._evaluate_hand_strength(player.hand.get_cards(), community_cards)
        pot_odds = self._calculate_pot_odds(game_state.table.total_pot, amount_to_call)
        win_probability = self._estimate_win_probability(player.hand.get_cards(), community_cards)
        ev = self._calculate_expected_value(hand_strength, pot_odds, amount_to_call, game_state.table.total_pot)

        action, amount = self._choose_ai_action(
            player, available_actions, amount_to_call, current_bet,
            hand_strength, game_state.state, pot_odds, win_probability, ev, game_state
        )

        return action, amount

    def _evaluate_hand_strength(self, hole_cards, community_cards):
        """
        评估手牌强度（0.0到1.0）

        Args:
            hole_cards: 底牌列表
            community_cards: 公共牌列表

        Returns:
            强度值（0.0弱到1.0强）
        """
        from texas_holdem.core.evaluator import PokerEvaluator

        if not hole_cards:
            return 0.5  # 默认中等强度

        all_cards = hole_cards + community_cards

        # 如果至少有5张牌，可以评估完整手牌
        if len(all_cards) >= 5:
            rank, values = PokerEvaluator.evaluate_hand(all_cards)
            # 将等级转换为强度（0-9等级，9是皇家同花顺）
            base_strength = rank / 9.0  # 0.0到1.0

            # 根据牌面值微调（高位牌更好）
            if values:
                high_card_bonus = values[0] / 14.0 * 0.2  # 最高牌面值奖励
                return min(1.0, base_strength + high_card_bonus)
            return base_strength
        else:
            # 翻牌前或公共牌不足：基于底牌评估
            return self._evaluate_preflop_strength(hole_cards)

    def _evaluate_preflop_strength(self, hole_cards):
        """
        评估翻牌前手牌强度

        Args:
            hole_cards: 底牌列表（2张）

        Returns:
            强度值（0.0到1.0）
        """
        if len(hole_cards) != 2:
            return 0.5

        card1, card2 = hole_cards
        val1, val2 = card1.value, card2.value

        # 对子
        if val1 == val2:
            # 高对子更好
            pair_strength = val1 / 14.0
            return 0.6 + pair_strength * 0.3  # 0.6到0.9

        # 同花
        suited = card1.suit == card2.suit

        # 连牌
        gap = abs(val1 - val2)
        connected = gap <= 2  # 间隔2张以内

        # 高牌
        high_card = max(val1, val2)
        high_strength = high_card / 14.0

        base = 0.3
        if suited:
            base += 0.1
        if connected:
            base += 0.1
        base += high_strength * 0.2

        return min(0.7, base)  # 翻牌前最大0.7（除非对子）

    def _calculate_pot_odds(self, total_pot, amount_to_call):
        """
        计算底池赔率

        Args:
            total_pot: 总底池
            amount_to_call: 需要跟注的金额

        Returns:
            底池赔率（需要跟注的金额/总底池，如果不需要跟注返回0）
        """
        if amount_to_call <= 0:
            return 0
        if total_pot == 0:
            return float('inf')  # 无穷大赔率
        return amount_to_call / total_pot

    def _estimate_win_probability(self, hole_cards, community_cards):
        """
        估算胜率（增强版）

        Args:
            hole_cards: 底牌列表
            community_cards: 公共牌列表

        Returns:
            胜率估计（0.0到1.0）
        """
        if not hole_cards:
            return 0.5

        # 根据公共牌数量选择计算方法
        num_community = len(community_cards)

        if num_community >= 3:
            # 有足够公共牌时使用蒙特卡洛模拟
            # 根据剩余牌的数量调整迭代次数
            iterations = 500 if num_community == 3 else 1000  # 翻牌圈500次，转牌河牌1000次
            win_prob = self._calculate_equity_monte_carlo(hole_cards, community_cards,
                                                         opponents=1, iterations=iterations)

            # 考虑outs（听牌概率）
            outs_info = self._calculate_outs(hole_cards, community_cards)
            total_outs = outs_info['total']

            # 根据outs调整胜率
            if total_outs > 0:
                # 计算改进概率：现有胜率 + outs带来的额外胜率
                cards_to_come = 5 - num_community  # 还要发多少张牌
                if cards_to_come == 2:  # 翻牌圈，还有2张牌
                    # 近似公式：胜率提高 ≈ outs * 4%
                    outs_bonus = total_outs * 0.04
                else:  # 转牌圈，还有1张牌
                    # 近似公式：胜率提高 ≈ outs * 2%
                    outs_bonus = total_outs * 0.02

                win_prob = min(0.95, win_prob + outs_bonus)

        else:
            # 翻牌前或公共牌不足：基于手牌强度估算胜率
            hand_strength = self._evaluate_hand_strength(hole_cards, community_cards)

            # 手牌强度转换为胜率（非线性映射，强牌胜率更高）
            if hand_strength > 0.8:
                win_prob = 0.7 + (hand_strength - 0.8) * 1.5  # 0.7到1.0
            elif hand_strength > 0.6:
                win_prob = 0.5 + (hand_strength - 0.6) * 1.0  # 0.5到0.7
            elif hand_strength > 0.4:
                win_prob = 0.3 + (hand_strength - 0.4) * 1.0  # 0.3到0.5
            else:
                win_prob = hand_strength * 0.75  # 0.0到0.3

            # 考虑公共牌数量：越多公共牌，估算越准确
            if num_community == 0:
                win_prob *= 0.8  # 翻牌前不确定性高
            elif num_community == 3:
                win_prob *= 0.9
            elif num_community >= 4:
                win_prob *= 1.0  # 转牌和河牌估算更准确

        return min(0.95, max(0.05, win_prob))  # 限制在5%-95%

    def _calculate_equity_monte_carlo(self, hole_cards: List[Card], community_cards: List[Card],
                                     opponents: int = 1, iterations: int = 1000) -> float:
        """
        使用蒙特卡洛模拟计算胜率（equity）

        Args:
            hole_cards: 底牌列表
            community_cards: 公共牌列表
            opponents: 对手数量（默认1）
            iterations: 模拟次数（默认1000）

        Returns:
            胜率估计（0.0到1.0）
        """
        if not hole_cards:
            return 0.5

        # 已知的牌
        known_cards = hole_cards + community_cards

        # 模拟结果计数
        wins = 0
        ties = 0

        for _ in range(iterations):
            # 生成剩余的牌堆
            deck = self._generate_remaining_deck(known_cards)
            random.shuffle(deck)

            # 补全公共牌
            remaining_community = 5 - len(community_cards)
            simulated_community = community_cards + deck[:remaining_community]
            deck = deck[remaining_community:]

            # 生成对手手牌
            opponent_hole_cards = []
            for _ in range(opponents):
                if len(deck) >= 2:
                    opponent_hole = deck[:2]
                    opponent_hole_cards.append(opponent_hole)
                    deck = deck[2:]

            # 如果无法生成足够的手牌，跳过这次模拟
            if len(opponent_hole_cards) < opponents:
                continue

            # 评估所有手牌
            player_cards = hole_cards + simulated_community
            player_rank, player_values = PokerEvaluator.evaluate_hand(player_cards)

            # 与每个对手比较
            player_wins = True
            player_ties = False

            for opp_hole in opponent_hole_cards:
                opp_cards = opp_hole + simulated_community
                opp_rank, opp_values = PokerEvaluator.evaluate_hand(opp_cards)

                if opp_rank > player_rank:
                    player_wins = False
                    break
                elif opp_rank == player_rank:
                    # 相同牌型，比较牌面值
                    comparison = 0
                    for pv, ov in zip(player_values, opp_values):
                        if pv > ov:
                            break
                        elif pv < ov:
                            comparison = -1
                            break

                    if comparison == -1:
                        player_wins = False
                        break
                    elif comparison == 0:
                        player_ties = True

            if player_wins:
                if player_ties:
                    ties += 1
                else:
                    wins += 1
            elif player_ties:
                ties += 0.5  # 平局算一半

        # 计算胜率：赢的次数 + 平局的一半
        equity = (wins + ties * 0.5) / iterations
        return equity

    def _generate_remaining_deck(self, known_cards: List[Card]) -> List[Card]:
        """
        生成剩余的牌堆（排除已知的牌）

        Args:
            known_cards: 已知的牌列表

        Returns:
            剩余的牌列表
        """
        # 创建已知牌的集合（使用rank和suit，因为Card构造函数需要这些）
        known_set = set((card.rank, card.suit) for card in known_cards)
        remaining = []

        # 花色映射
        suit_chars = ['H', 'D', 'C', 'S']  # 对应0,1,2,3

        # 牌面值映射
        value_to_rank = {
            2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '10',
            11: 'J', 12: 'Q', 13: 'K', 14: 'A'
        }

        for value in range(2, 15):  # 2到Ace (14)
            rank_str = value_to_rank[value]
            for suit_char in suit_chars:   # 4种花色
                if (rank_str, suit_char) not in known_set:
                    remaining.append(Card(suit_char, rank_str))

        return remaining

    def _calculate_outs(self, hole_cards: List[Card], community_cards: List[Card]) -> Dict[str, int]:
        """
        计算听牌张数（outs）

        Args:
            hole_cards: 底牌列表（2张）
            community_cards: 公共牌列表

        Returns:
            各种听牌的outs数量字典
        """
        if len(hole_cards) != 2 or not hole_cards:
            return {'total': 0, 'flush': 0, 'straight': 0, 'pair': 0}

        # 合并所有牌
        all_cards = hole_cards + community_cards

        # 计算同花听牌outs
        flush_outs = self._count_flush_outs(hole_cards, community_cards)

        # 计算顺子听牌outs
        straight_outs = self._count_straight_outs(hole_cards, community_cards)

        # 计算对子/三条/四条outs
        pair_outs = self._count_pair_outs(hole_cards, community_cards)

        # 去重：有些牌可能同时是多种听牌
        # 简单估计：总outs约等于各种outs之和的70%
        total_outs = int((flush_outs + straight_outs + pair_outs) * 0.7)

        return {
            'total': total_outs,
            'flush': flush_outs,
            'straight': straight_outs,
            'pair': pair_outs
        }

    def _count_flush_outs(self, hole_cards: List[Card], community_cards: List[Card]) -> int:
        """计算同花听牌outs"""
        if len(hole_cards) != 2:
            return 0

        # 统计花色
        suit_counts = {}
        for card in hole_cards + community_cards:
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1

        # 找出最多花色的牌数
        max_suit_count = max(suit_counts.values()) if suit_counts else 0
        max_suit = None
        for suit, count in suit_counts.items():
            if count == max_suit_count:
                max_suit = suit
                break

        if max_suit_count >= 5:  # 已经有同花
            return 0
        elif max_suit_count == 4:  # 差1张成同花
            # 还有13-4=9张该花色的牌在牌堆中
            return 9
        elif max_suit_count == 3:  # 差2张成同花
            # 翻牌圈：有9张outs；转牌圈：有10张outs（因为只剩1张牌要发）
            if len(community_cards) == 3:  # 翻牌圈
                return 9
            else:  # 转牌或河牌圈
                return 10
        else:
            return 0

    def _count_straight_outs(self, hole_cards: List[Card], community_cards: List[Card]) -> int:
        """计算顺子听牌outs"""
        if len(hole_cards) != 2:
            return 0

        # 收集所有牌面值
        all_values = set(card.value for card in hole_cards + community_cards)

        # 检查可能的顺子听牌
        straight_draws = []

        # 检查开端顺子（open-ended straight draw）
        for high_card in range(6, 15):  # 从6到A
            needed = set(range(high_card-4, high_card+1))
            missing = needed - all_values
            if len(missing) == 1:
                straight_draws.append(('open-ended', len(needed)))

        # 检查内听顺子（gut-shot straight draw）
        for high_card in range(5, 15):
            needed = set(range(high_card-4, high_card+1))
            missing = needed - all_values
            if len(missing) == 2:
                # 检查是否是内听顺子（中间缺一张）
                missing_list = sorted(list(missing))
                if len(missing_list) == 2:
                    # 简单判断：如果两张缺牌相邻或接近，可能是内听
                    straight_draws.append(('gut-shot', 4))

        # 估算outs：开端顺子通常8张outs，内听顺子4张outs
        outs = 0
        for draw_type, count in straight_draws:
            if draw_type == 'open-ended':
                outs += 8
            else:  # gut-shot
                outs += 4

        # 限制最大outs
        return min(outs, 12)

    def _count_pair_outs(self, hole_cards: List[Card], community_cards: List[Card]) -> int:
        """计算对子/三条/四条outs"""
        if len(hole_cards) != 2:
            return 0

        # 手牌值
        hole_values = [card.value for card in hole_cards]

        # 检查手牌是否已经是成牌
        if hole_values[0] == hole_values[1]:  # 口袋对
            # 口袋对可以提升为三条或四条
            pair_value = hole_values[0]

            # 检查公共牌中是否有相同的牌
            community_values = [card.value for card in community_cards]
            same_in_community = community_values.count(pair_value)

            if same_in_community == 0:  # 没有相同的牌
                # 2张outs成三条
                return 2
            elif same_in_community == 1:  # 已经有三条
                # 1张outs成四条
                return 1
            elif same_in_community == 2:  # 已经有四条
                return 0
        else:
            # 非对子手牌：可以成对、两对、三条
            # 每张底牌有3张outs成对
            outs = 6

            # 如果公共牌中已经有相同牌面值，减少outs
            community_values = [card.value for card in community_cards]
            for hole_value in hole_values:
                if hole_value in community_values:
                    outs -= 3  # 这张牌已经成对

            return max(0, outs)

    def _calculate_expected_value(self, hand_strength, pot_odds, amount_to_call, total_pot):
        """
        计算期望值（简化版）

        Args:
            hand_strength: 手牌强度
            pot_odds: 底池赔率
            amount_to_call: 需要跟注的金额
            total_pot: 总底池

        Returns:
            期望值估计
        """
        if amount_to_call <= 0:
            return total_pot * hand_strength  # 如果无需跟注，期望值是底池乘以胜率

        # 简化EV计算：EV = (胜率 * 可能赢得的底池) - (败率 * 需要跟注的金额)
        win_prob = hand_strength * 0.8  # 保守估计，手牌强度不完全等于胜率
        lose_prob = 1 - win_prob

        # 可能赢得的底池：当前底池 + 跟注金额
        potential_pot = total_pot + amount_to_call

        ev = (win_prob * potential_pot) - (lose_prob * amount_to_call)
        return ev

    def _should_bluff(self, game_state, hand_strength, position_factor, opponent_tendency=None, player_style='LAG'):
        """
        根据玩家风格决定是否诈唬

        Args:
            game_state: 游戏状态
            hand_strength: 手牌强度
            position_factor: 位置因子（0-1）
            opponent_tendency: 对手倾向字典（可选）
            player_style: 玩家打法风格

        Returns:
            是否应该诈唬
        """
        import random

        # 根据风格设置基础诈唬概率
        style_bluff_freq = {
            'TAG': 0.08,   # 紧凶 - 很少诈唬
            'LAG': 0.18,   # 松凶 - 经常诈唬
            'LAP': 0.05,   # 紧弱 - 极少诈唬
            'LP': 0.10     # 松弱 - 偶尔诈唬
        }
        base_bluff_chance = style_bluff_freq.get(player_style, 0.12)

        # 手牌强度调整
        strength_adjustment = (1.0 - hand_strength) * 0.06

        # 位置调整
        position_adjustment = position_factor * 0.05

        # 下注轮次调整
        street_adjustment = 0.0
        if game_state == 'pre_flop':
            street_adjustment = 0.02
        elif game_state in ['flop', 'turn']:
            street_adjustment = 0.05
        elif game_state == 'river':
            street_adjustment = 0.02

        # 对手倾向调整
        opponent_adjustment = 0.0
        if opponent_tendency:
            opp_style = opponent_tendency.get('style', 'Balanced')
            tightness = opponent_tendency.get('tightness', 'medium')

            if opp_style == 'TAG':
                opponent_adjustment = 0.05
            elif opp_style == 'LAG':
                opponent_adjustment = 0.02
            elif opp_style == 'Tight-Passive':
                opponent_adjustment = 0.08
            elif opp_style == 'Loose-Passive':
                opponent_adjustment = 0.03
            elif tightness in ['very_tight', 'tight']:
                opponent_adjustment = 0.05

        # 范围平衡
        random_adjustment = random.uniform(-0.05, 0.05)

        # 计算总诈唬概率
        total_bluff_chance = (base_bluff_chance + strength_adjustment +
                             position_adjustment + street_adjustment +
                             opponent_adjustment + random_adjustment)

        # 根据风格限制诈唬概率范围
        if player_style in ['TAG', 'LAP']:  # 紧的风格
            total_bluff_chance = max(0.05, min(0.25, total_bluff_chance))
        elif player_style == 'LAG':  # 松凶
            total_bluff_chance = max(0.15, min(0.40, total_bluff_chance))
        else:  # LP
            total_bluff_chance = max(0.05, min(0.20, total_bluff_chance))

        return random.random() < total_bluff_chance

    def _get_position_factor(self, player, game_state_manager):
        """
        计算位置因子（0-1，1表示位置最好）

        Args:
            player: 玩家
            game_state_manager: 游戏状态管理器

        Returns:
            位置因子
        """
        if not game_state_manager or not hasattr(game_state_manager, 'players'):
            return 0.5

        players = game_state_manager.players
        if len(players) != 2:
            return 0.5

        # 两人游戏：庄家位置最好
        if player.is_dealer:
            return 0.8
        else:
            return 0.2

    def _adjust_for_pot_odds(self, action_weights, pot_odds, win_probability, amount_to_call):
        """
        根据底池赔率调整行动权重

        Args:
            action_weights: 行动权重字典
            pot_odds: 底池赔率
            win_probability: 胜率估计
            amount_to_call: 需要跟注的金额

        Returns:
            调整后的行动权重
        """
        if amount_to_call <= 0 or pot_odds == 0:
            return action_weights

        # 如果胜率高于底池赔率，跟注是有利可图的
        if win_probability > pot_odds:
            # 增加跟注和加注权重
            action_weights['call'] = min(1.0, action_weights['call'] + 0.3)
            action_weights['raise'] = min(1.0, action_weights['raise'] + 0.2)
            # 减少弃牌权重
            action_weights['fold'] = max(0, action_weights['fold'] - 0.3)
        else:
            # 胜率低于赔率，倾向于弃牌
            action_weights['fold'] = min(1.0, action_weights['fold'] + 0.3)
            action_weights['call'] = max(0, action_weights['call'] - 0.2)
            action_weights['raise'] = max(0, action_weights['raise'] - 0.2)

        return action_weights

    def _choose_ai_action(self, player, available_actions, amount_to_call,
                         current_bet, hand_strength, game_state,
                         pot_odds=0, win_probability=0.5, ev=0, game_state_manager=None):
        """
        根据玩家风格选择AI行动
        
        支持风格：TAG(紧凶)、LAG(松凶)、LAP(紧弱)、LP(松弱)
        
        Returns:
            (行动, 金额) 元组
        """
        import random

        # 获取玩家风格配置
        style = getattr(player, 'ai_style', 'LAG')
        config = self.style_configs.get(style, self.style_configs['LAG'])

        # === 翻牌前严格起手牌选择（紧风格核心逻辑）===
        is_preflop = (game_state == GameState.PRE_FLOP or 
                      (isinstance(game_state, str) and 'pre' in game_state.lower()))
        
        if is_preflop and style in ['TAG', 'LAP']:
            # 紧风格：只玩前15-20%最强牌（手牌强度 >= 0.58）
            # 参考：AA=0.9, KK=0.88, QQ=0.86, JJ=0.84, TT=0.82
            #       99=0.71, 88=0.70, AKs=0.66, AQs=0.64, AKo=0.62
            #       AJo=0.58, KQs=0.58 - 这是紧风格的底线
            if hand_strength < 0.58:
                # 弱牌：通常弃牌
                if player.is_big_blind and amount_to_call <= 10:
                    # 大盲注位置，没人加注，可以免费看牌时：应该看牌，不弃牌！
                    # 已经投入大盲注，弃牌就是白白损失
                    return 'call', 0  # call 0 = check，免费看牌
                else:
                    # 其他位置需要跟注才能继续，直接弃牌
                    return 'fold', 0
            # 强牌（>=0.58）继续后续逻辑决定如何打
        
        elif is_preflop and style in ['LAG', 'LP']:
            # 松风格：玩前40-45%的牌（手牌强度 >= 0.35）
            if hand_strength < 0.35:
                if player.is_big_blind and amount_to_call <= 10:
                    # 大盲注可以免费看牌时，总是看牌不弃牌
                    return 'call', 0
                if random.random() < 0.75:  # 75%弃牌其他弱牌
                    return 'fold', 0
                else:
                    return 'call', 0

        # 基础行动权重
        action_weights = {
            'fold': 0,
            'check': 0,
            'call': 0,
            'bet': 0,
            'raise': 0,
            'all_in': 0
        }
        
        # 根据风格调整手牌强度阈值
        tightness_factor = {
            'TAG': 0.10,   # 紧凶 - 大幅提高标准
            'LAG': -0.05,  # 松凶 - 降低标准
            'LAP': 0.08,   # 紧弱 - 提高标准
            'LP': -0.08    # 松弱 - 降低标准
        }.get(style, 0)
        
        # 调整后的手牌强度阈值
        adjusted_strength = hand_strength - tightness_factor

        # 根据风格选择基础权重模板
        if adjusted_strength > 0.75:  # 超强牌
            if style in ['TAG', 'LAG']:  # 凶的风格
                action_weights['raise'] = 0.55
                action_weights['bet'] = 0.30
                action_weights['call'] = 0.15
            elif style == 'LAP':  # 紧弱 - 强牌也控制激进
                action_weights['raise'] = 0.15  # 很少加注
                action_weights['bet'] = 0.25    # 适度下注
                action_weights['call'] = 0.50   # 主要跟注
                action_weights['check'] = 0.10
            else:  # LP - 松弱
                action_weights['raise'] = 0.30
                action_weights['bet'] = 0.40
                action_weights['call'] = 0.30
        elif adjusted_strength > 0.55:  # 强牌
            if style in ['TAG', 'LAG']:  # 凶的风格
                action_weights['raise'] = 0.40
                action_weights['bet'] = 0.35
                action_weights['call'] = 0.25
            elif style == 'LAP':  # 紧弱 - 强牌也控制
                action_weights['raise'] = 0.10  # 很少加注
                action_weights['bet'] = 0.20    # 适度下注
                action_weights['call'] = 0.60   # 主要跟注
                action_weights['fold'] = 0.10
            else:  # LP - 松弱
                action_weights['raise'] = 0.15
                action_weights['bet'] = 0.30
                action_weights['call'] = 0.55
        elif adjusted_strength > 0.40:  # 中等牌
            if style == 'TAG':  # 紧凶 - 弃掉边缘牌
                action_weights['fold'] = 0.20
                action_weights['raise'] = 0.15
                action_weights['bet'] = 0.25
                action_weights['call'] = 0.40
            elif style == 'LAG':  # 松凶 - 继续施压
                action_weights['raise'] = 0.25
                action_weights['bet'] = 0.30
                action_weights['call'] = 0.35
                action_weights['fold'] = 0.10
            elif style == 'LAP':  # 紧弱 - 非常被动，很少加注
                action_weights['call'] = 0.70  # 主要跟注
                action_weights['fold'] = 0.20
                action_weights['bet'] = 0.05   # 极少主动下注
                action_weights['raise'] = 0.05  # 极少加注
            else:  # LP - 松弱 - 被动跟注
                action_weights['call'] = 0.65
                action_weights['fold'] = 0.15
                action_weights['bet'] = 0.15
                action_weights['raise'] = 0.05
        elif adjusted_strength > 0.30:  # 中等偏弱
            if style in ['TAG', 'LAP']:  # 紧的风格 - 弃牌
                action_weights['fold'] = 0.50
                action_weights['check'] = 0.30
                action_weights['call'] = 0.20
            else:  # 松的风格 - 跟注看牌
                action_weights['call'] = 0.50
                action_weights['check'] = 0.30
                action_weights['fold'] = 0.20
        else:  # 弱牌
            if style in ['TAG', 'LAP']:  # 紧的风格
                action_weights['fold'] = 0.70
                action_weights['check'] = 0.25
                action_weights['call'] = 0.05
            else:  # 松的风格
                action_weights['fold'] = 0.40
                action_weights['check'] = 0.35
                action_weights['call'] = 0.25

        # 2. 底池赔率调整（博弈论核心）
        action_weights = self._adjust_for_pot_odds(action_weights, pot_odds, win_probability, amount_to_call)

        # 2.5 听牌决策：翻牌后有听牌时，基于outs和赔率决定是否跟注
        if game_state in ['flop', 'turn'] and 'call' in available_actions and amount_to_call > 0:
            # 获取当前手牌和公共牌
            if game_state_manager:
                community_cards = game_state_manager.table.get_community_cards()
                if len(community_cards) >= 3:
                    # 获取玩家手牌
                    player_cards = player.hand.get_cards()
                    if len(player_cards) == 2:
                        # 计算听牌outs
                        outs_info = self._calculate_outs(player_cards, community_cards)
                        total_outs = outs_info['total']
                        
                        # 计算听牌胜率（简化公式：outs * 4% for flop, outs * 2% for turn）
                        cards_to_come = 5 - len(community_cards)
                        if cards_to_come == 2:  # 翻牌圈
                            draw_equity = min(0.95, total_outs * 0.04)
                        else:  # 转牌圈
                            draw_equity = min(0.95, total_outs * 0.02)
                        
                        # 计算需要的赔率
                        total_pot = game_state_manager.table.total_pot
                        pot_odds_needed = amount_to_call / (total_pot + amount_to_call) if (total_pot + amount_to_call) > 0 else 0
                        
                        # 如果听牌胜率高于底池赔率，应该跟注
                        if draw_equity > pot_odds_needed and draw_equity > 0.15:  # 至少15%胜率
                            # 增加跟注权重
                            action_weights['call'] = min(1.0, action_weights['call'] + 0.4)
                            action_weights['raise'] = min(1.0, action_weights['raise'] + 0.2)
                            action_weights['fold'] = max(0, action_weights['fold'] - 0.5)

        # 3. 期望值考虑
        if ev > 0:
            # 正期望值，增加积极行动权重
            action_weights['call'] = min(1.0, action_weights['call'] + 0.2)
            action_weights['raise'] = min(1.0, action_weights['raise'] + 0.1)
            action_weights['bet'] = min(1.0, action_weights['bet'] + 0.1)
        elif ev < -20:  # 显著负期望值
            # 负期望值，增加弃牌权重
            action_weights['fold'] = min(1.0, action_weights['fold'] + 0.3)
            action_weights['call'] = max(0, action_weights['call'] - 0.2)

        # 4. 诈唬策略（LAG风格：适度诈唬）
        position_factor = self._get_position_factor(player, game_state_manager)

        # 获取对手倾向（用于诈唬决策）
        opponent_tendency_for_bluff = None
        if game_state_manager and game_state_manager.players:
            for opponent in game_state_manager.players:
                if not opponent.is_ai and opponent.name in self.opponent_stats:
                    opponent_tendency_for_bluff = self._get_opponent_tendency(opponent.name)
                    break

        should_bluff = self._should_bluff(game_state, hand_strength, position_factor, opponent_tendency_for_bluff, style)

        if should_bluff and hand_strength < 0.35:  # 只有弱牌才诈唬
            # 根据风格调整诈唬强度
            bluff_multiplier = config.get('bluff_freq', 0.15) / 0.15  # 相对于基础15%
            bluff_strength = random.random() * 0.15 * bluff_multiplier
            action_weights['bet'] = min(1.0, action_weights['bet'] + bluff_strength)
            action_weights['raise'] = min(1.0, action_weights['raise'] + bluff_strength * 0.3)
            action_weights['fold'] = max(0, action_weights['fold'] - bluff_strength * 0.3)

        # 5. 位置优势（降低调整幅度）
        if position_factor > 0.6:  # 好位置（后位）
            # 后位适度激进
            action_weights['raise'] = min(1.0, action_weights['raise'] + 0.08)
            action_weights['bet'] = min(1.0, action_weights['bet'] + 0.05)
        else:  # 差位置（前位）
            # 前位更谨慎
            action_weights['raise'] = max(0, action_weights['raise'] - 0.15)
            action_weights['bet'] = max(0, action_weights['bet'] - 0.10)

        # 6. 下注轮次策略
        if game_state in ['flop', 'turn']:
            # 翻牌和转牌圈：更积极的策略
            if hand_strength > 0.65:  # 强牌 - 积极加注
                action_weights['raise'] = min(1.0, action_weights['raise'] + 0.35)
                action_weights['bet'] = min(1.0, action_weights['bet'] + 0.25)
            elif hand_strength > 0.5:  # 中等偏强 - 适度加注
                action_weights['raise'] = min(1.0, action_weights['raise'] + 0.20)
                action_weights['bet'] = min(1.0, action_weights['bet'] + 0.20)
            elif hand_strength > 0.35:  # 中等 - 小额下注或跟注
                action_weights['bet'] = min(1.0, action_weights['bet'] + 0.15)
                action_weights['call'] = min(1.0, action_weights['call'] + 0.20)
            else:  # 弱牌 - 少量诈唬
                if random.random() < 0.20:  # 20%诈唬
                    action_weights['bet'] = min(1.0, action_weights['bet'] + 0.25)
                    action_weights['raise'] = min(1.0, action_weights['raise'] + 0.10)
        
        elif game_state == 'river':
            # 河牌特殊策略
            import random
            
            # 需要下注/加注时的策略（两次价值一次诈唬）
            if 'bet' in available_actions or 'raise' in available_actions:
                if hand_strength > 0.55:  # 价值下注 (67%概率)
                    if random.random() < 0.67:
                        action_weights['bet'] = 0.8  # 高权重下注
                        action_weights['check'] = 0.2
                else:  # 诈唬下注 (33%概率)
                    if random.random() < 0.33:
                        action_weights['bet'] = 0.35  # 较低权重诈唬
                        action_weights['check'] = 0.65
                    else:
                        action_weights['check'] = 0.9  # 大部分时候过牌
            
            # 面对下注时的抓诈唬策略（一次抓一次不抓 = 50%）
            if amount_to_call > 0 and 'call' in available_actions:
                if hand_strength < 0.4:  # 弱牌时考虑抓诈唬
                    # 直接使用概率控制，覆盖其他权重
                    if random.random() < 0.4:  # 40%概率直接抓诈唬
                        return 'call', 0  # 直接返回跟注
                    else:
                        action_weights['fold'] = 0.75
                        action_weights['call'] = 0.25

        # 7. 对手倾向调整
        # 获取对手倾向（假设只有一个人类对手）
        if game_state_manager and game_state_manager.players:
            for opponent in game_state_manager.players:
                if not opponent.is_ai and opponent.name in self.opponent_stats:
                    opponent_tendency = self._get_opponent_tendency(opponent.name)
                    action_weights = self._adjust_for_opponent_tendency(action_weights, opponent_tendency)
                    break  # 只考虑第一个人类对手

        # 9. 根据当前下注状态调整行动
        if current_bet == 0:
            # 没有下注时：不能加注，只能下注
            action_weights['raise'] = 0
            # 如果没有下注，下注权重增加
            if 'bet' in available_actions:
                action_weights['bet'] = min(1.0, action_weights['bet'] + 0.3)
        else:
            # 已有下注时：不能下注，只能加注
            # 将 bet 的权重转移到 raise
            bet_weight = action_weights.get('bet', 0)
            action_weights['raise'] = min(1.0, action_weights['raise'] + bet_weight * 0.8)
            action_weights['bet'] = 0

        # 10. 筹码管理：如果需要跟注的金额很大，倾向于弃牌（但优先考虑过牌）
        if amount_to_call > 0:
            call_ratio = amount_to_call / max(player.chips, 1)
            if call_ratio > 0.5:  # 需要跟注超过筹码一半
                # 如果有check选项（免费看牌），绝不增加弃牌权重
                if 'check' not in available_actions:
                    action_weights['fold'] = min(1.0, action_weights['fold'] + 0.4)
                    action_weights['call'] = max(0, action_weights['call'] - 0.3)
                # 如果可以check，保持现有权重，让后续逻辑决定
            elif call_ratio > 0.3:  # 需要跟注超过30%
                if 'check' not in available_actions:
                    action_weights['fold'] = min(1.0, action_weights['fold'] + 0.2)
                    action_weights['call'] = max(0, action_weights['call'] - 0.1)

        # 11. 过滤不可用行动
        for action in list(action_weights.keys()):
            if action not in available_actions:
                action_weights[action] = 0

        # 12. 关键规则：如果有过牌选项，根据牌力和位置决定是否下注
        # 翻牌后、转牌、河牌都可以主动下注（价值或诈唬）
        if 'check' in available_actions:
            import random
            
            # 可以下注时的决策
            if 'bet' in available_actions:
                # 根据手牌强度决定是否下注
                if hand_strength > 0.6:  # 强牌 - 价值下注
                    if random.random() < 0.7:  # 70%概率下注
                        amount = self._calculate_bet_amount(
                            'bet', player, current_bet, amount_to_call,
                            hand_strength, win_probability, pot_odds, game_state, game_state_manager
                        )
                        return 'bet', amount
                    return 'check', 0
                    
                elif hand_strength > 0.4:  # 中等牌 - 小额试探或 check
                    if random.random() < 0.3:  # 30%概率下注
                        amount = self._calculate_bet_amount(
                            'bet', player, current_bet, amount_to_call,
                            hand_strength, win_probability, pot_odds, game_state, game_state_manager
                        )
                        return 'bet', amount
                    return 'check', 0
                    
                else:  # 弱牌 - 偶尔诈唬
                    if random.random() < 0.25:  # 25%概率诈唬
                        amount = self._calculate_bet_amount(
                            'bet', player, current_bet, amount_to_call,
                            hand_strength, win_probability, pot_odds, game_state, game_state_manager
                        )
                        return 'bet', amount
                    return 'check', 0
            else:
                # 不能下注时，永远过牌
                return 'check', 0

        # 13. 归一化权重
        total_weight = sum(action_weights.values())
        if total_weight == 0:
            # 默认：优先过牌，其次跟注，最后弃牌
            if 'check' in available_actions:
                return 'check', 0  # 没人下注时，免费看牌
            elif 'call' in available_actions:
                return 'call', 0
            else:
                return 'fold', 0

        # 14. 根据权重随机选择
        r = random.random() * total_weight
        cumulative = 0
        for action, weight in action_weights.items():
            cumulative += weight
            if r <= cumulative and weight > 0:
                # 确定金额（整合概率因素）
                amount = self._calculate_bet_amount(
                    action, player, current_bet, amount_to_call,
                    hand_strength, win_probability, pot_odds, game_state, game_state_manager
                )
                # 修复：如果加注金额计算为0或小于最小加注额，改为跟注
                if action == 'raise' and amount <= 0:
                    if 'call' in available_actions:
                        return 'call', 0
                    else:
                        return 'check', 0
                return action, amount

        # 15. 回退：优先过牌，其次跟注，最后弃牌
        if 'check' in available_actions:
            return 'check', 0  # 没人下注时，绝不弃牌
        elif 'call' in available_actions:
            return 'call', 0
        else:
            return 'fold', 0

    def _calculate_bet_amount(self, action, player, current_bet, amount_to_call,
                             hand_strength, win_probability, pot_odds, game_state='flop', game_state_manager=None):
        """
        LAG风格下注金额计算 - 适中但持续施压
        翻牌前限制在3-5个大盲（60-100筹码）

        Args:
            action: 行动类型
            player: 玩家
            current_bet: 当前下注额
            amount_to_call: 需要跟注的金额
            hand_strength: 手牌强度
            win_probability: 胜率估计
            pot_odds: 底池赔率
            game_state: 游戏状态（翻牌前特殊处理）
            game_state_manager: 游戏状态管理器（用于获取min_raise）

        Returns:
            下注金额
        """
        if action not in ['bet', 'raise']:
            return 0

        import random
        from texas_holdem.utils import constants as _game_constants

        # 翻牌前特殊处理：限制加注在3-5个大盲
        is_preflop = (game_state == 'pre_flop' or 
                      (isinstance(game_state, str) and 'pre' in game_state.lower()))
        
        # 获取当前大盲注值（支持盲注升级）
        BIG_BLIND_VALUE = _game_constants.BIG_BLIND
        
        if is_preflop:
            # 翻牌前：降低加注频率，更保守的加注大小
            if action == 'raise':
                # 前面有人加注过吗？
                has_raise_before = current_bet > BIG_BLIND_VALUE * 2
                
                # 如果有人已经加注过，降低再加注的概率（通过返回较小的加注额）
                if has_raise_before and hand_strength < 0.6:
                    # 没好牌时，很少再加注（3bet/4bet）
                    if random.random() < 0.7:  # 70%概率改为跟注
                        return 0  # 返回0表示最小加注，但后续会被过滤为call
                
                # 基础加注额：2-3BB（降低）
                base_min_raise = BIG_BLIND_VALUE * 2
                max_raise_add = BIG_BLIND_VALUE * 3
                
                # 只有强牌才加注更多
                if hand_strength > 0.75:
                    max_raise_add = BIG_BLIND_VALUE * 4
                
                # 如果前面有人加注过，使用min_raise
                actual_min_raise = base_min_raise
                if game_state_manager and hasattr(game_state_manager, 'min_raise'):
                    actual_min_raise = max(base_min_raise, game_state_manager.min_raise)
                
                # 确保最小不超过最大
                if actual_min_raise > max_raise_add:
                    max_raise_add = actual_min_raise + BIG_BLIND_VALUE
                
                # 随机选择加注大小
                raise_amount = random.randint(actual_min_raise, max_raise_add)
                raise_amount = max(BIG_BLIND_VALUE, min(raise_amount, player.chips - amount_to_call))
                
                return raise_amount
            else:  # bet
                # 翻牌前bet：2.5-3.5个大盲（降低）
                amount = random.randint(int(BIG_BLIND_VALUE * 2.5), int(BIG_BLIND_VALUE * 3.5))
                return max(20, min(amount, player.chips))

        # 翻牌后：基于底池大小的下注
        # 获取真实底池大小
        if game_state_manager and hasattr(game_state_manager, 'table'):
            pot_size = game_state_manager.table.total_pot
        else:
            pot_size = current_bet * 3 if current_bet > 0 else 60  # 估算底池
        
        if action == 'bet':
            # 基于底池比例的下注尺度
            # 小注: 1/3底池, 中注: 1/2底池, 大注: 2/3底池, 超大注: 1底池
            if hand_strength > 0.75:  # 超强牌 - 大注索取价值
                bet_ratio = 0.75  # 3/4底池
            elif hand_strength > 0.60:  # 强牌 - 中等偏大注
                bet_ratio = 0.66  # 2/3底池
            elif hand_strength > 0.45:  # 中等牌 - 标准注
                bet_ratio = 0.50  # 1/2底池
            elif hand_strength > 0.35:  # 弱牌 - 小注或诈唬
                bet_ratio = 0.33  # 1/3底池
            else:  # 极弱牌 - 小额诈唬
                bet_ratio = 0.25 if random.random() < 0.3 else 0  # 25%底池或放弃
            
            # 根据胜率微调
            win_adjust = (win_probability - 0.5) * 0.2
            bet_ratio = max(0.25, min(1.0, bet_ratio + win_adjust))
            
            amount = int(pot_size * bet_ratio)
            min_amount = max(int(pot_size * 0.25), 20)  # 最小1/4底池
            max_amount = min(player.chips, int(pot_size * 1.5))  # 最大1.5倍底池
            
            amount = max(min_amount, min(amount, max_amount))
            return amount
            
        else:  # raise
            # 加注：基于当前需要跟注的金额 + 底池的一定比例
            # 标准加注：跟注额 + 1/2到2/3底池
            base_raise = amount_to_call
            
            if hand_strength > 0.70:  # 强牌 - 大加注施压
                additional = int(pot_size * 0.75)
            elif hand_strength > 0.55:  # 中等强牌
                additional = int(pot_size * 0.60)
            elif hand_strength > 0.40:  # 中等牌
                additional = int(pot_size * 0.45)
            else:  # 弱牌 - 小加注或诈唬
                additional = int(pot_size * 0.30) if random.random() < 0.4 else int(pot_size * 0.25)
            
            amount = base_raise + additional
            min_amount = max(amount_to_call + int(pot_size * 0.25), amount_to_call * 2)
            max_amount = min(player.chips - amount_to_call, int(pot_size * 1.5))
            
            amount = max(min_amount, min(amount, max_amount))
            
            # 极少全押
            if random.random() < 0.03 and (hand_strength > 0.8 or hand_strength < 0.2):
                amount = player.chips - amount_to_call
            
            if amount > player.chips - amount_to_call:
                amount = player.chips - amount_to_call
                
            return amount

    def _initialize_opponent_stats(self, players: List[Player]):
        """
        初始化对手统计数据

        Args:
            players: 玩家列表
        """
        for player in players:
            if not player.is_ai:  # 人类玩家是AI的对手
                self.opponent_stats[player.name] = {
                    'vpip': 0.0,      # 主动投入底池频率
                    'pfr': 0.0,       # 翻牌前加注频率
                    'af': 0.0,        # 激进因子
                    'hands_played': 0, # 玩的手牌数
                    'preflop_actions': 0,
                    'preflop_raises': 0,
                    'voluntary_put': 0,
                    'total_hands': 0
                }

    def _update_opponent_stats(self, player_name: str, action: str, street: str, amount: int = 0):
        """
        更新对手统计数据

        Args:
            player_name: 玩家名称
            action: 行动（fold, check, call, bet, raise, all_in）
            street: 下注轮次（preflop, flop, turn, river）
            amount: 下注金额（可选）
        """
        if player_name not in self.opponent_stats:
            return

        stats = self.opponent_stats[player_name]

        # 更新总手牌数
        if street == 'preflop' and action != 'fold':
            stats['total_hands'] += 1

        # 更新翻牌前统计
        if street == 'preflop':
            stats['preflop_actions'] += 1

            if action in ['bet', 'raise']:
                stats['preflop_raises'] += 1

            if action != 'fold':
                stats['voluntary_put'] += 1

        # 计算VPIP（主动投入底池频率）
        if street == 'preflop' and action != 'fold':
            stats['hands_played'] += 1

        # 更新VPIP和PFR（每10手牌更新一次）
        if stats['total_hands'] >= 10:
            if stats['total_hands'] > 0:
                stats['vpip'] = stats['hands_played'] / stats['total_hands']
            if stats['preflop_actions'] > 0:
                stats['pfr'] = stats['preflop_raises'] / stats['preflop_actions']

        # 计算激进因子（AF）
        if street != 'preflop':
            # 简化计算：激进行动次数 / 被动行动次数
            # 这里需要更多数据，暂时简单处理
            pass

    def _get_opponent_tendency(self, player_name: str) -> Dict[str, str]:
        """
        获取对手倾向分析

        Args:
            player_name: 玩家名称

        Returns:
            倾向分析字典
        """
        if player_name not in self.opponent_stats:
            return {'style': 'unknown', 'aggression': 'neutral', 'tightness': 'medium'}

        stats = self.opponent_stats[player_name]

        # 基于VPIP和PFR判断玩家风格
        vpip = stats.get('vpip', 0)
        pfr = stats.get('pfr', 0)

        # 判断松紧程度
        if vpip < 0.15:
            tightness = 'very_tight'
        elif vpip < 0.25:
            tightness = 'tight'
        elif vpip < 0.35:
            tightness = 'medium'
        elif vpip < 0.45:
            tightness = 'loose'
        else:
            tightness = 'very_loose'

        # 判断激进程度（基于PFR/VPIP比例）
        if vpip > 0:
            pfr_vpip_ratio = pfr / vpip
            if pfr_vpip_ratio > 0.6:
                aggression = 'aggressive'
            elif pfr_vpip_ratio > 0.4:
                aggression = 'neutral'
            else:
                aggression = 'passive'
        else:
            aggression = 'neutral'

        # 综合风格
        if tightness in ['very_tight', 'tight'] and aggression == 'aggressive':
            style = 'TAG'  # 紧凶
        elif tightness in ['very_tight', 'tight'] and aggression in ['neutral', 'passive']:
            style = 'Tight-Passive'
        elif tightness in ['loose', 'very_loose'] and aggression == 'aggressive':
            style = 'LAG'  # 松凶
        elif tightness in ['loose', 'very_loose'] and aggression in ['neutral', 'passive']:
            style = 'Loose-Passive'
        else:
            style = 'Balanced'

        return {
            'style': style,
            'aggression': aggression,
            'tightness': tightness,
            'vpip': vpip,
            'pfr': pfr
        }

    def _adjust_for_opponent_tendency(self, action_weights: Dict[str, float],
                                     opponent_tendency: Dict[str, str]) -> Dict[str, float]:
        """
        根据对手倾向调整行动权重

        Args:
            action_weights: 原始行动权重
            opponent_tendency: 对手倾向分析

        Returns:
            调整后的行动权重
        """
        style = opponent_tendency.get('style', 'Balanced')
        aggression = opponent_tendency.get('aggression', 'neutral')
        tightness = opponent_tendency.get('tightness', 'medium')

        adjusted_weights = action_weights.copy()

        # 根据对手风格调整策略
        if style == 'TAG':  # 紧凶玩家
            # 紧凶玩家弃牌率高，可以多诈唬
            adjusted_weights['bet'] = min(1.0, adjusted_weights['bet'] + 0.1)
            adjusted_weights['raise'] = min(1.0, adjusted_weights['raise'] + 0.05)
            # 减少跟注权重，因为对手下注代表强牌
            adjusted_weights['call'] = max(0, adjusted_weights['call'] - 0.1)

        elif style == 'LAG':  # 松凶玩家
            # 松凶玩家诈唬多，用中等以上牌跟注/加注
            adjusted_weights['call'] = min(1.0, adjusted_weights['call'] + 0.1)
            adjusted_weights['raise'] = min(1.0, adjusted_weights['raise'] + 0.1)
            # 减少诈唬权重，因为对手可能跟注
            adjusted_weights['bet'] = max(0, adjusted_weights['bet'] - 0.05)

        elif style == 'Tight-Passive':  # 紧弱玩家
            # 紧弱玩家只在有强牌时下注，可以多偷盲
            adjusted_weights['bet'] = min(1.0, adjusted_weights['bet'] + 0.15)
            adjusted_weights['raise'] = min(1.0, adjusted_weights['raise'] + 0.1)
            # 如果他们加注，很可能有强牌，减少跟注权重
            adjusted_weights['call'] = max(0, adjusted_weights['call'] - 0.15)

        elif style == 'Loose-Passive':  # 松弱玩家
            # 松弱玩家跟注多，诈唬少，用强牌价值下注
            adjusted_weights['bet'] = min(1.0, adjusted_weights['bet'] + 0.2)
            adjusted_weights['raise'] = min(1.0, adjusted_weights['raise'] + 0.15)
            # 减少诈唬，因为他们可能跟注

        return adjusted_weights

    def display_rules(self):
        """显示游戏规则"""
        print("\n" + "=" * 60)
        print("德州扑克规则说明")
        print("=" * 60)
        print("\n游戏流程:")
        print("1. 每手牌开始前，庄家位置轮转")
        print("2. 庄家左侧的玩家发布小盲注")
        print("3. 小盲注左侧的玩家发布大盲注")
        print("4. 每位玩家发2张底牌")
        print("5. 进行翻牌前下注（从大盲注后玩家开始）")
        print("6. 发出3张翻牌（公共牌）")
        print("7. 进行翻牌圈下注")
        print("8. 发出1张转牌（第4张公共牌）")
        print("9. 进行转牌圈下注")
        print("10. 发出1张河牌（第5张公共牌）")
        print("11. 进行河牌圈下注")
        print("12. 摊牌比较手牌（如果有多于一个玩家未弃牌）")
        print("\n手牌等级 (从高到低):")
        print("  1. 皇家同花顺")
        print("  2. 同花顺")
        print("  3. 四条")
        print("  4. 葫芦")
        print("  5. 同花")
        print("  6. 顺子")
        print("  7. 三条")
        print("  8. 两对")
        print("  9. 一对")
        print("  10. 高牌")
        print("\n可用行动:")
        print("  • 弃牌(fold/f): 放弃当前手牌")
        print("  • 过牌(check/c/k): 不下注（如果不需要跟注）")
        print("  • 跟注(call/c): 下注到当前下注额")
        print("  • 下注(bet/b [金额]): 开始下注（如果没有当前下注）")
        print("  • 加注(raise/r [金额]): 增加下注额")
        print("  • 全押(allin/a): 下注所有剩余筹码")
        print("\n" + "=" * 60)