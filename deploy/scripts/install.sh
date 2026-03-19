#!/bin/bash
################################################################################
# YOLO 检测推流服务 - Ubuntu 部署安装脚本
# 适用于配置较低的 Ubuntu 服务器
################################################################################

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 配置变量
PROJECT_NAME="yolo-detect"
INSTALL_DIR="/opt/$PROJECT_NAME"
SERVICE_NAME="yolo-streaming"
USER=$(whoami)
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$CURRENT_DIR")"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}YOLO 检测推流服务 - 安装脚本${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}请使用 sudo 运行此脚本${NC}"
    exit 1
fi

# 检测系统
if [ ! -f /etc/os-release ]; then
    echo -e "${RED}无法检测操作系统类型${NC}"
    exit 1
fi

source /etc/os-release
echo -e "${YELLOW}检测到系统: $PRETTY_NAME${NC}"

# 1. 安装系统依赖
echo ""
echo -e "${GREEN}[1/6] 安装系统依赖...${NC}"
apt-get update
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    ffmpeg \
    v4l-utils \
    usbutils \
    systemd \
    libopencv-dev \
    python3-opencv

# 2. 复制项目文件
echo ""
echo -e "${GREEN}[2/6] 复制项目文件...${NC}"
mkdir -p "$INSTALL_DIR"

# 复制整个项目
cp -r "$PROJECT_ROOT"/* "$INSTALL_DIR/"
cp -r "$PROJECT_ROOT"/.venv "$INSTALL_DIR/" 2>/dev/null || true

# 3. 安装 Python 依赖（使用已有的虚拟环境）
echo ""
echo -e "${GREEN}[3/6] 配置 Python 环境...${NC}"
cd "$INSTALL_DIR"

if [ ! -d ".venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv .venv
fi

echo "激活虚拟环境并安装依赖..."
source .venv/bin/activate
pip install --upgrade pip

# 如果有 pyproject.toml，使用 poetry
if [ -f "pyproject.toml" ]; then
    pip install poetry
    poetry install --no-interaction
else
    pip install -r requirements.txt 2>/dev/null || true
fi

# 确保 PIL 支持中文
pip install pillow

# 4. 设置权限
echo ""
echo -e "${GREEN}[4/6] 设置文件权限...${NC}"
chown -R $USER:$USER "$INSTALL_DIR"
chmod +x "$INSTALL_DIR/deploy/scripts"/*.sh

# 5. 安装 Systemd 服务
echo ""
echo -e "${GREEN}[5/6] 安装系统服务...${NC}"

# 读取配置
source "$INSTALL_DIR/deploy/config/service.conf"

# 设置模型预设（根据服务器配置自动选择）
if [ -z "$MODEL_PRESET" ]; then
    # 检测系统内存
    TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
    TOTAL_MEM_MB=$((TOTAL_MEM_KB / 1024))

    if [ $TOTAL_MEM_MB -lt 1024 ]; then
        MODEL_PRESET="performance"
        echo -e "${YELLOW}检测到低内存配置 (<1GB)，使用性能优先预设${NC}"
    elif [ $TOTAL_MEM_MB -lt 2048 ]; then
        MODEL_PRESET="standard"
        echo -e "${YELLOW}检测到中等内存配置 (<2GB)，使用标准预设${NC}"
    else
        MODEL_PRESET="standard"
        echo -e "${GREEN}检测到充足内存 (>=2GB)，使用标准预设${NC}"
    fi

    # 更新配置文件
    sed -i "s/^MODEL_PRESET=.*/MODEL_PRESET=\"$MODEL_PRESET\"/" "$INSTALL_DIR/deploy/config/service.conf"
fi

# 创建服务文件
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=YOLO Detection and Streaming Service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$INSTALL_DIR
Environment="PATH=$INSTALL_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
Environment="PROJECT_DIR=$INSTALL_DIR"
ExecStart=$INSTALL_DIR/.venv/bin/python $INSTALL_DIR/deploy/scripts/start_service.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# 资源限制（低配置服务器）
MemoryMax=1G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

# 重载 systemd
systemctl daemon-reload

# 6. 检测摄像头
echo ""
echo -e "${GREEN}[6/6] 检测摄像头设备...${NC}"
bash "$INSTALL_DIR/deploy/scripts/detect_camera.sh"

# 完成
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "项目目录: ${YELLOW}$INSTALL_DIR${NC}"
echo -e "服务名称: ${YELLOW}$SERVICE_NAME${NC}"
echo ""
echo -e "常用命令:"
echo -e "  启动服务: ${YELLOW}sudo systemctl start $SERVICE_NAME${NC}"
echo -e "  停止服务: ${YELLOW}sudo systemctl stop $SERVICE_NAME${NC}"
echo -e "  重启服务: ${YELLOW}sudo systemctl restart $SERVICE_NAME${NC}"
echo -e "  开机自启: ${YELLOW}sudo systemctl enable $SERVICE_NAME${NC}"
echo -e "  查看日志: ${YELLOW}sudo journalctl -u $SERVICE_NAME -f${NC}"
echo ""
echo -e "配置文件: ${YELLOW}$INSTALL_DIR/deploy/config/service.conf${NC}"
echo -e "修改配置后请重启服务: ${YELLOW}sudo systemctl restart $SERVICE_NAME${NC}"
echo ""
