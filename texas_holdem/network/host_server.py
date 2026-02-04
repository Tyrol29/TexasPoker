"""
房主服务端
作为游戏主机，管理房间和转发游戏状态
"""

import socket
import threading
import time
from typing import Dict, List, Callable, Optional, Tuple
from .protocol import MessageType, GameMessage, encode_game_state_for_network


class PlayerConnection:
    """玩家连接封装"""
    
    def __init__(self, socket: socket.socket, addr: Tuple[str, int], name: str):
        self.socket = socket
        self.addr = addr
        self.name = name
        self.connected = True
        self.is_ready = False
        self.hand_cards = []  # 该玩家的手牌（服务器记录）
        self.receive_thread: Optional[threading.Thread] = None
    
    def send_message(self, msg: GameMessage) -> bool:
        """发送消息给该玩家"""
        try:
            data = msg.to_json().encode('utf-8')
            length = len(data)
            self.socket.sendall(length.to_bytes(4, 'big'))
            self.socket.sendall(data)
            return True
        except:
            self.connected = False
            return False
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        try:
            self.socket.close()
        except:
            pass


class HostServer:
    """房主服务器类"""
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8888):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.running = False
        
        # 连接管理
        self.players: Dict[str, PlayerConnection] = {}  # name -> connection
        self.max_players = 7  # 房主 + 7个远程 = 最多8人
        
        # 回调函数
        self.on_player_join: Optional[Callable[[str], None]] = None
        self.on_player_leave: Optional[Callable[[str], None]] = None
        self.on_action_received: Optional[Callable[[str, str, int], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        
        # 游戏状态
        self.game_started = False
        self.current_turn_player: Optional[str] = None
        self.turn_start_time: Optional[float] = None
        self.turn_timeout = 15  # 每回合15秒
        
        # 倒计时线程
        self.timer_thread: Optional[threading.Thread] = None
        self.timer_running = False
    
    def start(self) -> bool:
        """启动服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(self.max_players)
            
            self.running = True
            
            # 启动接受连接线程
            accept_thread = threading.Thread(target=self._accept_loop)
            accept_thread.daemon = True
            accept_thread.start()
            
            return True
        except Exception as e:
            if self.on_error:
                self.on_error(f"启动服务器失败: {e}")
            return False
    
    def stop(self):
        """停止服务器"""
        self.running = False
        self.timer_running = False
        
        # 断开所有玩家
        for player in list(self.players.values()):
            player.disconnect()
        self.players.clear()
        
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def get_player_list(self) -> List[str]:
        """获取玩家列表"""
        return list(self.players.keys())
    
    def broadcast(self, msg: GameMessage, exclude: Optional[str] = None):
        """广播消息给所有玩家"""
        for name, player in self.players.items():
            if name != exclude and player.connected:
                player.send_message(msg)
    
    def send_to(self, player_name: str, msg: GameMessage) -> bool:
        """发送消息给指定玩家"""
        if player_name in self.players:
            return self.players[player_name].send_message(msg)
        return False
    
    def start_game(self):
        """开始游戏"""
        self.game_started = True
        msg = GameMessage(MessageType.GAME_START, {})
        self.broadcast(msg)
    
    def broadcast_game_state(self, game_state, players, current_player_name: str):
        """广播游戏状态"""
        # 计算剩余时间
        remaining_time = self.turn_timeout
        if self.turn_start_time and current_player_name == self.current_turn_player:
            elapsed = time.time() - self.turn_start_time
            remaining_time = max(0, self.turn_timeout - int(elapsed))
        
        state_data = encode_game_state_for_network(
            game_state, players, current_player_name, remaining_time
        )
        
        msg = GameMessage(MessageType.GAME_STATE, state_data)
        self.broadcast(msg)
        
        # 发送手牌给各个玩家
        for p in players:
            if p.name in self.players and not p.is_ai:
                hand_msg = GameMessage(
                    MessageType.PLAYER_HAND,
                    {'hand': [c.__dict__ if hasattr(c, '__dict__') else str(c) for c in p.hand.get_cards()]},
                    p.name
                )
                self.players[p.name].send_message(hand_msg)
    
    def notify_turn(self, player_name: str):
        """通知轮到某玩家行动"""
        self.current_turn_player = player_name
        self.turn_start_time = time.time()
        
        if player_name in self.players:
            # 远程玩家
            msg = GameMessage(MessageType.YOUR_TURN, {'timeout': self.turn_timeout})
            self.players[player_name].send_message(msg)
            
            # 启动倒计时
            self._start_turn_timer(player_name)
    
    def _start_turn_timer(self, player_name: str):
        """启动回合倒计时"""
        self.timer_running = False
        time.sleep(0.1)  # 确保旧线程退出
        
        self.timer_running = True
        self.timer_thread = threading.Thread(target=self._turn_timer, args=(player_name,))
        self.timer_thread.daemon = True
        self.timer_thread.start()
    
    def _turn_timer(self, player_name: str):
        """倒计时线程"""
        start_time = time.time()
        
        while self.timer_running and self.current_turn_player == player_name:
            elapsed = time.time() - start_time
            remaining = self.turn_timeout - elapsed
            
            if remaining <= 0:
                # 超时，自动弃牌
                if self.on_action_received:
                    self.on_action_received(player_name, 'fold', 0)
                break
            
            # 每秒检查一次
            time.sleep(0.5)
    
    def _accept_loop(self):
        """接受连接循环"""
        while self.running:
            try:
                self.socket.settimeout(1.0)  # 1秒超时以便检查running状态
                client_socket, addr = self.socket.accept()
                
                if not self.running:
                    break
                
                # 检查是否已满
                if len(self.players) >= self.max_players:
                    # 发送拒绝消息
                    msg = GameMessage(
                        MessageType.ERROR,
                        {'message': '房间已满'}
                    )
                    client_socket.send(msg.to_json().encode('utf-8'))
                    client_socket.close()
                    continue
                
                # 新线程处理连接
                handler_thread = threading.Thread(
                    target=self._handle_new_connection,
                    args=(client_socket, addr)
                )
                handler_thread.daemon = True
                handler_thread.start()
                
            except socket.timeout:
                continue
            except:
                break
    
    def _handle_new_connection(self, client_socket: socket.socket, addr):
        """处理新连接"""
        try:
            # 设置超时等待玩家名称
            client_socket.settimeout(5.0)
            
            # 接收连接请求（包含玩家名称）
            length_bytes = self._recv_all(client_socket, 4)
            if not length_bytes:
                client_socket.close()
                return
            
            length = int.from_bytes(length_bytes, 'big')
            data = self._recv_all(client_socket, length)
            if not data:
                client_socket.close()
                return
            
            msg = GameMessage.from_json(data.decode('utf-8'))
            if msg.msg_type != MessageType.CONNECT:
                client_socket.close()
                return
            
            player_name = msg.data.get('player_name', '')
            
            # 检查名称是否已存在
            if player_name in self.players:
                ack_msg = GameMessage(
                    MessageType.CONNECT_ACK,
                    {'success': False, 'message': '名称已被使用'}
                )
                client_socket.sendall(len(ack_msg.to_json()).to_bytes(4, 'big'))
                client_socket.sendall(ack_msg.to_json().encode('utf-8'))
                client_socket.close()
                return
            
            # 检查游戏是否已开始
            if self.game_started:
                ack_msg = GameMessage(
                    MessageType.CONNECT_ACK,
                    {'success': False, 'message': '游戏已开始'}
                )
                client_socket.sendall(len(ack_msg.to_json()).to_bytes(4, 'big'))
                client_socket.sendall(ack_msg.to_json().encode('utf-8'))
                client_socket.close()
                return
            
            # 创建玩家连接
            client_socket.settimeout(None)
            player_conn = PlayerConnection(client_socket, addr, player_name)
            self.players[player_name] = player_conn
            
            # 发送确认
            ack_msg = GameMessage(
                MessageType.CONNECT_ACK,
                {'success': True, 'message': '连接成功'}
            )
            player_conn.send_message(ack_msg)
            
            # 广播玩家加入
            join_msg = GameMessage(
                MessageType.PLAYER_JOIN,
                {'player_name': player_name, 'player_count': len(self.players)}
            )
            self.broadcast(join_msg)
            
            # 通知回调
            if self.on_player_join:
                self.on_player_join(player_name)
            
            # 启动接收循环
            self._player_receive_loop(player_name)
            
        except Exception as e:
            if self.on_error:
                self.on_error(f"处理连接失败: {e}")
    
    def _player_receive_loop(self, player_name: str):
        """玩家消息接收循环"""
        player = self.players.get(player_name)
        if not player:
            return
        
        while self.running and player.connected:
            try:
                # 接收长度
                length_bytes = self._recv_all(player.socket, 4)
                if not length_bytes:
                    break
                
                length = int.from_bytes(length_bytes, 'big')
                data = self._recv_all(player.socket, length)
                if not data:
                    break
                
                msg = GameMessage.from_json(data.decode('utf-8'))
                self._handle_player_message(player_name, msg)
                
            except Exception:
                break
        
        # 玩家断开
        self._player_disconnect(player_name)
    
    def _handle_player_message(self, player_name: str, msg: GameMessage):
        """处理玩家消息"""
        if msg.msg_type == MessageType.PLAYER_ACTION:
            # 玩家操作
            action = msg.data.get('action', '')
            amount = msg.data.get('amount', 0)
            
            if self.on_action_received:
                self.on_action_received(player_name, action, amount)
        
        elif msg.msg_type == MessageType.PING:
            # 心跳响应
            pong_msg = GameMessage(MessageType.PONG, {})
            self.players[player_name].send_message(pong_msg)
    
    def _player_disconnect(self, player_name: str):
        """玩家断开连接"""
        if player_name not in self.players:
            return
        
        player = self.players[player_name]
        player.disconnect()
        del self.players[player_name]
        
        # 广播玩家离开
        leave_msg = GameMessage(
            MessageType.PLAYER_LEAVE,
            {'player_name': player_name, 'player_count': len(self.players)}
        )
        self.broadcast(leave_msg)
        
        # 通知回调
        if self.on_player_leave:
            self.on_player_leave(player_name)
    
    def _recv_all(self, sock: socket.socket, n: int) -> Optional[bytes]:
        """接收指定长度数据"""
        data = b''
        while len(data) < n:
            try:
                sock.settimeout(5.0)
                packet = sock.recv(n - len(data))
                if not packet:
                    return None
                data += packet
            except:
                return None
        return data
