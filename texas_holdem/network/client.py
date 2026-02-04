"""
游戏客户端
用于连接房主服务器，接收游戏状态并发送操作
"""

import socket
import threading
import time
from typing import Callable, Optional
from .protocol import MessageType, GameMessage


class GameClient:
    """游戏客户端类"""
    
    def __init__(self, player_name: str):
        self.player_name = player_name
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.server_addr = None
        
        # 回调函数
        self.on_state_update: Optional[Callable[[dict], None]] = None
        self.on_your_turn: Optional[Callable[[int], None]] = None  # 参数为剩余秒数
        self.on_room_info: Optional[Callable[[dict], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None
        self.on_disconnect: Optional[Callable[[], None]] = None
        self.on_game_start: Optional[Callable[[], None]] = None
        
        # 接收线程
        self.receive_thread: Optional[threading.Thread] = None
        self.running = False
        
        # 当前游戏状态
        self.current_state: Optional[dict] = None
        self.my_hand: Optional[list] = None
    
    def connect(self, host: str, port: int = 8888) -> bool:
        """连接到房主服务器"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(5)  # 连接超时5秒
            self.socket.connect((host, port))
            self.socket.settimeout(None)  # 连接成功后取消超时
            
            self.server_addr = (host, port)
            
            # 发送连接请求
            connect_msg = GameMessage(
                MessageType.CONNECT,
                {'player_name': self.player_name},
                self.player_name
            )
            self._send_message(connect_msg)
            
            # 等待确认
            response = self._receive_message()
            if response and response.msg_type == MessageType.CONNECT_ACK:
                self.connected = True
                self.running = True
                
                # 启动接收线程
                self.receive_thread = threading.Thread(target=self._receive_loop)
                self.receive_thread.daemon = True
                self.receive_thread.start()
                
                return True
            else:
                self.socket.close()
                return False
                
        except Exception as e:
            if self.on_error:
                self.on_error(f"连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        self.running = False
        self.connected = False
        
        if self.socket:
            try:
                msg = GameMessage(MessageType.DISCONNECT, {}, self.player_name)
                self._send_message(msg)
                self.socket.close()
            except:
                pass
            self.socket = None
    
    def send_action(self, action: str, amount: int = 0) -> bool:
        """发送玩家操作"""
        if not self.connected:
            return False
        
        msg = GameMessage(
            MessageType.PLAYER_ACTION,
            {'action': action, 'amount': amount},
            self.player_name
        )
        return self._send_message(msg)
    
    def _send_message(self, msg: GameMessage) -> bool:
        """发送消息"""
        try:
            data = msg.to_json().encode('utf-8')
            # 先发送长度（4字节），再发送数据
            length = len(data)
            self.socket.sendall(length.to_bytes(4, 'big'))
            self.socket.sendall(data)
            return True
        except Exception as e:
            self.connected = False
            if self.on_error:
                self.on_error(f"发送消息失败: {e}")
            return False
    
    def _receive_message(self) -> Optional[GameMessage]:
        """接收一条消息"""
        try:
            # 先接收长度（4字节）
            length_bytes = self._recv_all(4)
            if not length_bytes:
                return None
            length = int.from_bytes(length_bytes, 'big')
            
            # 接收数据
            data = self._recv_all(length)
            if not data:
                return None
            
            return GameMessage.from_json(data.decode('utf-8'))
        except Exception:
            return None
    
    def _recv_all(self, n: int) -> Optional[bytes]:
        """接收指定长度的数据"""
        data = b''
        while len(data) < n:
            try:
                packet = self.socket.recv(n - len(data))
                if not packet:
                    return None
                data += packet
            except:
                return None
        return data
    
    def _receive_loop(self):
        """接收消息循环（在后台线程运行）"""
        while self.running:
            msg = self._receive_message()
            if not msg:
                if self.running:
                    # 连接断开
                    self.connected = False
                    if self.on_disconnect:
                        self.on_disconnect()
                break
            
            self._handle_message(msg)
    
    def _handle_message(self, msg: GameMessage):
        """处理接收到的消息"""
        if msg.msg_type == MessageType.GAME_STATE:
            self.current_state = msg.data
            if self.on_state_update:
                self.on_state_update(msg.data)
        
        elif msg.msg_type == MessageType.YOUR_TURN:
            timeout = msg.data.get('timeout', 15)
            if self.on_your_turn:
                self.on_your_turn(timeout)
        
        elif msg.msg_type == MessageType.ROOM_INFO:
            if self.on_room_info:
                self.on_room_info(msg.data)
        
        elif msg.msg_type == MessageType.GAME_START:
            if self.on_game_start:
                self.on_game_start()
        
        elif msg.msg_type == MessageType.ERROR:
            error_msg = msg.data.get('message', '未知错误')
            if self.on_error:
                self.on_error(error_msg)
        
        elif msg.msg_type == MessageType.PLAYER_HAND:
            # 服务器发来的手牌信息
            self.my_hand = msg.data.get('hand', [])
