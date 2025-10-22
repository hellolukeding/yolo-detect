#!/bin/bash
# FFmpeg 推流快速部署脚本 - x86_64 Ubuntu

set -e

echo "╔═══════════════════════════════════════════════════════╗"
echo "║       FFmpeg 推流系统快速部署                         ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# 检查系统
ARCH=$(uname -m)
echo "系统架构: $ARCH"
echo "操作系统: $(lsb_release -d | cut -f2)"
echo ""

# 步骤 1: 安装 FFmpeg
echo "================================================"
echo "步骤 1/4: 安装 FFmpeg"
echo "================================================"

if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg 已安装: $(ffmpeg -version | head -n1)"
else
    echo "正在安装 FFmpeg..."
    sudo apt-get update
    sudo apt-get install -y ffmpeg
    echo "✅ FFmpeg 安装完成"
fi

echo ""

# 步骤 2: 安装项目依赖
echo "================================================"
echo "步骤 2/4: 安装项目依赖"
echo "================================================"

if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry 未安装，请先运行:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

poetry install
echo "✅ 项目依赖安装完成"
echo ""

# 步骤 3: 检查摄像头
echo "================================================"
echo "步骤 3/4: 检查摄像头设备"
echo "================================================"

if ls /dev/video* 1> /dev/null 2>&1; then
    echo "✅ 找到摄像头设备:"
    ls -l /dev/video*
else
    echo "⚠️  未找到摄像头设备"
fi

echo ""

# 步骤 4: 验证安装
echo "================================================"
echo "步骤 4/4: 验证安装"
echo "================================================"

echo "检查 Python 依赖:"
poetry run python -c "
import cv2
import numpy as np
from ultralytics import YOLO
print(f'  ✅ OpenCV: {cv2.__version__}')
print(f'  ✅ NumPy: {np.__version__}')
print('  ✅ Ultralytics YOLO')
"

echo ""
echo "检查 FFmpeg 编码器:"
if ffmpeg -encoders 2>/dev/null | grep -q libx264; then
    echo "  ✅ libx264 (H.264 编码器)"
else
    echo "  ❌ libx264 未找到"
fi

echo ""
echo "╔═══════════════════════════════════════════════════════╗"
echo "║              部署完成！                                ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""
echo "下一步:"
echo "  1. 编辑配置: nano test/test_push_ffmpeg.py"
echo "     - 修改 host='YOUR_SERVER_IP'"
echo "     - 修改 camera_device='/dev/videoX'"
echo ""
echo "  2. 测试推流: poetry run python test/test_push_ffmpeg.py"
echo ""
echo "  3. 查看文档: cat FFMPEG_STREAMING.md"
echo ""
echo "提示: FFmpeg 方案不需要 OpenCV GStreamer 支持！"
echo ""
