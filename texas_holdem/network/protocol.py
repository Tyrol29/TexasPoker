"""
网络通信协议
定义联机游戏的消息格式和类型
"""

import json
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class MessageType(Enum):
    """消息类型"""
    # 连接相关
    CONNECT = "connect"           # 客户端请求连接
    CONNECT_ACK = "connect_ack"   # 服务器确认连接
    DISCONNECT = "disconnect"     # 断开连接
    
    # 房间管理
    ROOM_INFO = "room_info"       # 房间信息（玩家列表等）
    PLAYER_JOIN = "player_join"   # 玩家加入
    PLAYER_LEAVE = "player_leave" # 玩家离开
    GAME_START = "game_start"     # 游戏开始
    
    # 游戏状态
    GAME_STATE = "game_state"     # 完整游戏状态广播
    YOUR_TURN = "your_turn"       # 轮到某玩家行动
    PLAYER_HAND = "player_hand"   # 玩家手牌（只发给对应玩家）
    
    # 玩家操作
    PLAYER_ACTION = "player_action"  # 玩家执行操作
    ACTION_RESULT = "action_result"  # 操作结果
    
    # 超时处理
    TURN_TIMEOUT = "turn_timeout"    # 回合超时警告
    AUTO_FOLD = "auto_fold"          # 自动弃牌
    
    # 错误处理
    ERROR = "error"               # 错误消息
    PING = "ping"                 # 心跳检测
    PONG = "pong"                 # 心跳响应


@dataclass
class GameMessage:
    """游戏消息类"""
    msg_type: MessageType
    data: Dict[str, Any]
    sender: str = ""  # 发送者名称
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps({
            'type': self.msg_type.value,
            'data': self.data,
            'sender': self.sender
        }, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'GameMessage':
        """从JSON字符串解析"""
        try:
            obj = json.loads(json_str)
            return cls(
                msg_type=MessageType(obj.get('type')),
                data=obj.get('data', {}),
                sender=obj.get('sender', '')
            )
        except (json.JSONDecodeError, ValueError) as e:
            return cls(MessageType.ERROR, {'error': str(e)})


# 游戏状态序列化/反序列化辅助函数

def encode_game_state_for_network(game_state, players, current_player_name: str, 
                                   timeout: int = 15) -> Dict[str, Any]:
    """
    将游戏状态编码为网络传输格式
    注意：手牌信息会根据玩家分别发送
    """
    from ..utils.save_manager import GameStateEncoder
    
    # 基础游戏状态
    state_data = {
        'state': game_state.state,
        'current_player_index': game_state.current_player_index,
        'current_bet': game_state.current_bet,
        'min_raise': game_state.min_raise,
        'hand_number': game_state.hand_number,
        'current_player': current_player_name,
        'timeout': timeout,
    }
    
    # 公共牌
    state_data['community_cards'] = [
        GameStateEncoder.encode_card(c) for c in game_state.table.get_community_cards()
    ]
    
    # 底池信息
    state_data['total_pot'] = game_state.table.total_pot
    state_data['side_pots'] = [
        {'amount': pot.amount, 'eligible': list(pot.eligible_players)}
        for pot in game_state.table.side_pots
    ]
    
    # 玩家信息（不包含手牌，手牌单独处理）
    state_data['players'] = []
    for p in players:
        player_info = {
            'name': p.name,
            'chips': p.chips,
            'bet_amount': p.bet_amount,
            'is_active': p.is_active,
            'is_all_in': p.is_all_in,
            'is_ai': p.is_ai,
            'is_dealer': p.is_dealer,
            'is_small_blind': p.is_small_blind,
            'is_big_blind': p.is_big_blind,
        }
        state_data['players'].append(player_info)
    
    return state_data


def decode_game_state_from_network(state_data: Dict[str, Any]) -> Dict[str, Any]:
    """从网络格式解码游戏状态"""
    return state_data


def encode_player_hand(player) -> Dict[str, Any]:
    """编码玩家手牌（只发给对应玩家）"""
    from ..utils.save_manager import GameStateEncoder
    return {
        'name': player.name,
        'hand': GameStateEncoder.encode_hand(player.hand)
    }
