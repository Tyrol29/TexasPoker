"""
扑克牌类
表示一张标准的扑克牌，包含花色和牌面值
"""

class Card:
    # 花色映射（使用ASCII字符避免编码问题）
    SUITS = {
        'H': 'H',  # 红桃
        'D': 'D',  # 方块
        'C': 'C',  # 梅花
        'S': 'S'   # 黑桃
    }

    # 花色符号（用于显示，如果需要Unicode符号）
    SUIT_SYMBOLS = {
        'H': '♥',  # 红桃
        'D': '♦',  # 方块
        'C': '♣',  # 梅花
        'S': '♠'   # 黑桃
    }

    # ANSI 颜色代码 - 四种花色四种颜色
    COLORS = {
        'red': '\033[91m',      # 亮红色 - 红桃
        'yellow': '\033[93m',   # 亮黄色 - 方块
        'green': '\033[92m',    # 亮绿色 - 梅花
        'cyan': '\033[96m',     # 亮青色 - 黑桃
        'reset': '\033[0m'      # 重置
    }

    # 花色颜色映射（四种花色四种不同颜色）
    SUIT_COLORS = {
        'H': 'red',     # 红桃 - 红色
        'D': 'yellow',  # 方块 - 黄色
        'C': 'green',   # 梅花 - 绿色
        'S': 'cyan'     # 黑桃 - 青色
    }

    # 牌面值映射
    RANKS = {
        '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
        'J': 11, 'Q': 12, 'K': 13, 'A': 14
    }

    # 反向映射用于显示
    RANK_TO_STR = {
        2: '2', 3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: '10',
        11: 'J', 12: 'Q', 13: 'K', 14: 'A'
    }

    def __init__(self, suit: str, rank: str):
        """
        初始化一张扑克牌

        Args:
            suit: 花色 ('H', 'D', 'C', 'S')
            rank: 牌面值 ('2'-'10', 'J', 'Q', 'K', 'A')
        """
        if suit not in self.SUITS:
            raise ValueError(f"Invalid suit: {suit}. Must be one of {list(self.SUITS.keys())}")
        if rank not in self.RANKS:
            raise ValueError(f"Invalid rank: {rank}. Must be one of {list(self.RANKS.keys())}")

        self.suit = suit
        self.rank = rank
        self.value = self.RANKS[rank]

    def __repr__(self):
        return f"Card('{self.suit}', '{self.rank}')"

    def __str__(self, use_symbols=False, use_color=True):
        """
        返回扑克牌的字符串表示
        
        Args:
            use_symbols: 是否使用Unicode花色符号（♥♦♣♠）
            use_color: 是否使用颜色（红桃方块=红色，黑桃梅花=白色）
        """
        if use_symbols:
            suit_symbol = self.SUIT_SYMBOLS[self.suit]
        else:
            suit_symbol = self.SUITS[self.suit]
        rank_str = self.rank if len(self.rank) <= 2 else self.rank
        
        if use_color:
            color_key = self.SUIT_COLORS[self.suit]
            color_code = self.COLORS[color_key]
            reset_code = self.COLORS['reset']
            return f"{color_code}{rank_str}{suit_symbol}{reset_code}"
        else:
            return f"{rank_str}{suit_symbol}"

    def __eq__(self, other):
        if not isinstance(other, Card):
            return False
        return self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return hash((self.suit, self.rank))

    def __lt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.value < other.value

    def __le__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.value <= other.value

    def __gt__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.value > other.value

    def __ge__(self, other):
        if not isinstance(other, Card):
            return NotImplemented
        return self.value >= other.value

    def to_dict(self):
        """转换为字典表示"""
        return {'suit': self.suit, 'rank': self.rank}

    @classmethod
    def from_dict(cls, data):
        """从字典创建Card对象"""
        return cls(data['suit'], data['rank'])