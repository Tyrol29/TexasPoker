# Ubuntu 安装说明

## 方法一：直接使用 Python 运行（推荐）

### 1. 安装 Python 和依赖
```bash
sudo apt update
sudo apt install python3 python3-pip git -y
```

### 2. 下载游戏
```bash
git clone https://github.com/Tyrol29/TexesPoker.git
cd TexesPoker
```

### 3. 安装 Python 依赖
```bash
pip3 install -r requirements.txt
```

### 4. 运行游戏
```bash
python3 texas_holdem/main.py
```

---

## 方法二：使用打包好的 Linux 可执行文件

### 下载
从 GitHub Releases 下载 `texas-holdem-linux` 文件

### 赋予执行权限
```bash
chmod +x texas-holdem-linux
```

### 运行
```bash
./texas-holdem-linux
```

---

## 方法三：自行打包

```bash
# 安装 PyInstaller
pip3 install pyinstaller

# 打包
pyinstaller --onefile --console \
  --hidden-import texas_holdem.core.card \
  --hidden-import texas_holdem.core.deck \
  --hidden-import texas_holdem.core.hand \
  --hidden-import texas_holdem.core.player \
  --hidden-import texas_holdem.core.table \
  --hidden-import texas_holdem.core.evaluator \
  --hidden-import texas_holdem.game.game_state \
  --hidden-import texas_holdem.game.betting \
  --hidden-import texas_holdem.game.game_engine \
  --hidden-import texas_holdem.ui.cli \
  --hidden-import texas_holdem.utils.constants \
  --hidden-import texas_holdem.network \
  --name texas-holdem \
  texas_holdem/main.py

# 运行
./dist/texas-holdem
```

---

## 联机对战注意事项

### 防火墙设置
Ubuntu 默认防火墙可能阻止连接，需要开放端口：

```bash
# 开放 8888 端口
sudo ufw allow 8888/tcp

# 或者临时关闭防火墙（测试用）
sudo ufw disable
```

### IPv6 支持
Ubuntu 通常默认支持 IPv6，可通过以下命令检查：

```bash
# 检查 IPv6 地址
ip addr show | grep inet6

# 测试 IPv6 连接
curl -6 https://test-ipv6.com
```

### 网络模式选择

1. **局域网** - 同一 WiFi 下直接使用 IPv4
2. **IPv6 直连** - 如果双方都有公网 IPv6，可直接连接
3. **内网穿透** - 使用 ngrok 等工具

```bash
# Ubuntu 安装 ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin/

# 运行 ngrok
ngrok tcp 8888
```

---

## 常见问题

### Q: 运行时报错 `ModuleNotFoundError`
确保安装了所有依赖：
```bash
pip3 install -r requirements.txt
```

### Q: 终端显示乱码
设置 UTF-8 编码：
```bash
export LANG=en_US.UTF-8
export PYTHONIOENCODING=utf-8
```

### Q: 无法创建房间（端口被占用）
检查端口占用：
```bash
sudo lsof -i :8888
# 或更换端口运行（需修改代码）
```

### Q: Windows 玩家无法连接我的 Ubuntu 房间
1. 确保防火墙已放行
2. 检查是否在同一网络（或使用 IPv6/内网穿透）
3. 确认 Ubuntu 的 IP 地址正确

---

## 系统要求

- Ubuntu 18.04+ / Debian 10+ / 其他 Linux 发行版
- Python 3.8+（方法一和方法三）
- 或不依赖 Python（方法二，使用打包版本）
- 网络连接（联机模式需要）
