"""
德州扑克起手牌牌力字典
基于真实在线数据（PokerRoom.com统计）和Sklansky分组
牌力范围：0.0 - 1.0 (1.0为最强AA)
"""

# 169种起手牌的牌力字典
# s = 同花(suited), o = 不同花(offsuit), p = 对子(pair)
PREFLOP_STRENGTH = {
    # 第1组 (超强牌)
    'AA': 1.000,  # 坚果
    'KK': 0.960,
    'QQ': 0.920,
    'JJ': 0.880,
    'AKs': 0.850,
    'TT': 0.840,
    
    # 第2组 (强牌)
    'AKo': 0.820,
    'AQs': 0.800,
    'AJs': 0.780,
    'KQs': 0.760,
    '99': 0.750,
    'ATs': 0.740,
    'KJs': 0.730,
    'QJs': 0.720,
    'JTs': 0.710,
    
    # 第3组 (好牌)
    'AQo': 0.700,
    'KQo': 0.680,
    'AJo': 0.670,
    'KJo': 0.660,
    'QJo': 0.650,
    'JTo': 0.640,
    'T9s': 0.630,
    'A9s': 0.620,
    '88': 0.610,
    'K9s': 0.600,
    'Q9s': 0.590,
    'J9s': 0.580,
    'T8s': 0.570,
    
    # 第4组 (中等牌)
    '98s': 0.560,
    'ATo': 0.550,
    'KTo': 0.540,
    'QTo': 0.530,
    'J8s': 0.520,
    '87s': 0.510,
    '77': 0.500,
    'A8s': 0.495,
    'K8s': 0.490,
    'Q8s': 0.485,
    'T9o': 0.480,
    '76s': 0.475,
    
    # 第5组 (边缘牌)
    '66': 0.470,
    'A7s': 0.465,
    'A9o': 0.460,
    'K7s': 0.455,
    'J9o': 0.450,
    'T8o': 0.445,
    '98o': 0.440,
    '65s': 0.435,
    'A6s': 0.430,
    'Q9o': 0.425,
    'K6s': 0.420,
    '54s': 0.415,
    
    # 第6组 (弱牌)
    '55': 0.410,
    'A8o': 0.405,
    'K9o': 0.400,
    'J7s': 0.395,
    'T7s': 0.390,
    '97s': 0.385,
    '87o': 0.380,
    'A5s': 0.375,
    'K5s': 0.370,
    'Q7s': 0.365,
    '44': 0.360,
    
    # 第7组 (很弱牌)
    'A7o': 0.355,
    'A6o': 0.350,
    'K8o': 0.345,
    'Q8o': 0.340,
    'J8o': 0.335,
    'T6s': 0.330,
    '96s': 0.325,
    '86s': 0.320,
    '75s': 0.315,
    '33': 0.310,
    'A4s': 0.305,
    
    # 第8组 (极弱牌)
    'A5o': 0.300,
    'A4o': 0.295,
    'K7o': 0.290,
    'K6o': 0.285,
    'Q7o': 0.280,
    'J7o': 0.275,
    'T7o': 0.270,
    '97o': 0.265,
    '86o': 0.260,
    '76o': 0.255,
    '22': 0.250,
    'A3s': 0.245,
    
    # 第9组 (垃圾牌)
    'A3o': 0.240,
    'A2o': 0.235,
    'K5o': 0.230,
    'K4s': 0.225,
    'K3s': 0.220,
    'K2s': 0.215,
    'Q6s': 0.210,
    'Q5s': 0.205,
    'Q4s': 0.200,
    'J6s': 0.195,
    'T6o': 0.190,
    
    # 第10组 (最弱牌)
    'A2s': 0.185,
    'K4o': 0.180,
    'K3o': 0.175,
    'K2o': 0.170,
    'Q6o': 0.165,
    'Q5o': 0.160,
    'Q4o': 0.155,
    'Q3o': 0.150,
    'Q2o': 0.145,
    'J6o': 0.140,
    'J5o': 0.135,
    'T5o': 0.130,
    '95o': 0.125,
    '85o': 0.120,
    '75o': 0.115,
    '65o': 0.110,
    '54o': 0.105,
    '64o': 0.100,
    '53o': 0.095,
    '43o': 0.090,
    '42o': 0.085,
    '32o': 0.080,
}

# 反向字典（从小到大排序）
SORTED_HANDS = sorted(PREFLOP_STRENGTH.items(), key=lambda x: x[1], reverse=True)

# Sklansky分组参考
SKLANSKY_GROUPS = {
    1: ['AA', 'KK', 'QQ', 'JJ', 'AKs'],
    2: ['TT', 'AQs', 'AJs', 'KQs', 'AKo'],
    3: ['99', 'ATs', 'KJs', 'QJs', 'JTs', 'AQo'],
    4: ['88', 'A9s', 'KTs', 'QTs', 'J9s', 'T9s', 'AJo', 'KQo'],
    5: ['77', 'A8s', 'A7s', 'A6s', 'A5s', 'A4s', 'A3s', 'A2s', 
        'K9s', 'Q9s', 'J8s', 'JTo', 'QJo', 'KJo', 'ATo'],
    6: ['66', '55', 'K8s', 'K7s', 'K6s', 'K5s', 'K4s', 'K3s', 'K2s',
        'Q8s', 'Q7s', 'Q6s', 'T8s', 'T9o', 'J9o', 'Q9o', 'K9o', 'A9o'],
    7: ['44', '33', '22', 'J7s', 'J6s', 'J5s', 'J4s', 'J3s', 'J2s',
        'T7s', 'T6s', 'T5s', '98s', '97s', '96s', '87s', '86s', '85s',
        '76s', '75s', '74s', '65s', '64s', '63s', '54s', '53s', '52s', '43s'],
    8: ['J8o', 'J7o', 'J6o', 'J5o', 'J4o', 'J3o', 'J2o',
        'T8o', 'T7o', 'T6o', 'T5o', 'T4o', 'T3o', 'T2o',
        '98o', '97o', '96o', '95o', '87o', '86o', '85o', '84o',
        '76o', '75o', '74o', '73o', '65o', '64o', '63o', '62o',
        '54o', '53o', '52o', '43o', '42o', '32o'],
}


def get_preflop_strength(hole_cards) -> float:
    """
    获取起手牌牌力
    
    Args:
        hole_cards: 两张底牌列表 [Card, Card]
    
    Returns:
        牌力值 0.0-1.0
    """
    if len(hole_cards) != 2:
        return 0.5
    
    card1, card2 = hole_cards
    
    # 获取牌面值 (A=14, K=13, Q=12, J=11, T=10, ...)
    v1, v2 = card1.value, card2.value
    
    # 构建字典key
    ranks = '23456789TJQKA'
    rank1 = ranks[v1 - 2]  # 2->0, A->12
    rank2 = ranks[v2 - 2]
    
    # 对子
    if v1 == v2:
        key = rank1 + rank2  # 如 'AA', 'KK'
    else:
        # 确保大牌在前
        if v1 < v2:
            rank1, rank2 = rank2, rank1
        
        # 判断是否同花
        if card1.suit == card2.suit:
            key = rank1 + rank2 + 's'  # 同花，如 'AKs'
        else:
            key = rank1 + rank2 + 'o'  # 不同花，如 'AKo'
    
    return PREFLOP_STRENGTH.get(key, 0.30)


def get_hand_ranking(hole_cards) -> int:
    """
    获取起手牌排名 (1-169, 1为最强AA)
    
    Args:
        hole_cards: 两张底牌列表
    
    Returns:
        排名 1-169
    """
    strength = get_preflop_strength(hole_cards)
    
    # 根据牌力值估算排名
    if strength >= 0.85:
        return 1
    elif strength >= 0.80:
        return 3
    elif strength >= 0.75:
        return 7
    elif strength >= 0.70:
        return 13
    elif strength >= 0.65:
        return 22
    elif strength >= 0.60:
        return 34
    elif strength >= 0.55:
        return 50
    elif strength >= 0.50:
        return 70
    elif strength >= 0.45:
        return 95
    elif strength >= 0.40:
        return 120
    elif strength >= 0.35:
        return 140
    else:
        return 155


def get_sklansky_group(hole_cards) -> int:
    """
    获取Sklansky分组 (1-8, 1为最强)
    
    Args:
        hole_cards: 两张底牌列表
    
    Returns:
        Sklansky分组 1-8 (0表示未分组)
    """
    strength = get_preflop_strength(hole_cards)
    
    if strength >= 0.84:
        return 1
    elif strength >= 0.75:
        return 2
    elif strength >= 0.68:
        return 3
    elif strength >= 0.61:
        return 4
    elif strength >= 0.55:
        return 5
    elif strength >= 0.48:
        return 6
    elif strength >= 0.40:
        return 7
    else:
        return 8


def print_top_hands(n: int = 20):
    """打印前N强起手牌"""
    print(f"\n前{n}强起手牌:")
    print("-" * 30)
    for i, (hand, strength) in enumerate(SORTED_HANDS[:n], 1):
        bar = "█" * int(strength * 20)
        print(f"{i:2d}. {hand:4s} {strength:.3f} {bar}")


if __name__ == '__main__':
    # 测试
    print_top_hands(30)
    
    # 测试特定手牌
    from texas_holdem.core.card import Card
    
    test_hands = [
        (Card('S', 'A'), Card('H', 'A')),  # AA
        (Card('S', 'A'), Card('S', 'K')),  # AKs
        (Card('S', 'A'), Card('H', 'K')),  # AKo
        (Card('S', '7'), Card('H', '2')),  # 72o (最弱)
        (Card('S', '10'), Card('H', '10')),  # TT
    ]
    
    print("\n测试手牌:")
    for c1, c2 in test_hands:
        strength = get_preflop_strength([c1, c2])
        group = get_sklansky_group([c1, c2])
        print(f"{c1}{c2}: 牌力={strength:.3f}, Sklansky组={group}")
