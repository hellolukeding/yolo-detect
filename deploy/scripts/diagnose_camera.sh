#!/bin/bash
################################################################################
# 摄像头诊断脚本
# 用于排查 RealSense 和 USB 摄像头问题
################################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}摄像头诊断工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 检查 USB 设备
echo -e "${GREEN}[1] USB 设备列表${NC}"
if lsusb 2>/dev/null | grep -qi "real\|camera\|cam"; then
    echo -e "${YELLOW}检测到的摄像头相关设备:${NC}"
    lsusb | grep -i "real\|camera\|cam\|0b03\|0b07\|0b0a\|0b48\|0b49\|0b4b\|0b4d\|0b5a" || true
else
    echo -e "${RED}未找到摄像头相关 USB 设备${NC}"
fi
echo ""

# 2. 检查 Intel 设备
echo -e "${GREEN}[2] Intel 设备 (RealSense)${NC}"
if lsusb 2>/dev/null | grep -i "intel"; then
    echo -e "${YELLOW}Intel 设备:${NC}"
    lsusb | grep -i "intel" || true
else
    echo -e "${YELLOW}未找到 Intel 设备${NC}"
fi
echo ""

# 3. 检查视频设备
echo -e "${GREEN}[3] 视频 (/dev/video) 设备${NC}"
VIDEO_COUNT=0
for i in {0..10}; do
    if [ -e "/dev/video$i" ]; then
        VIDEO_COUNT=$((VIDEO_COUNT + 1))
        DEVICE_INFO=$(v4l2-ctl --device=/dev/video$i --info 2>/dev/null || true)
        NAME=$(echo "$DEVICE_INFO" | grep "Card type" | cut -d: -f2 | xargs || echo "Unknown")
        echo -e "  /dev/video$i - $NAME"

        # 检查驱动
        DRIVER=$(echo "$DEVICE_INFO" | grep "Driver name" | cut -d: -f2 | xargs || echo "Unknown")
        echo -e "    驱动: $DRIVER"
    fi
done

if [ $VIDEO_COUNT -eq 0 ]; then
    echo -e "${RED}未找到任何视频设备${NC}"
else
    echo -e "${GREEN}共找到 $VIDEO_COUNT 个视频设备${NC}"
fi
echo ""

# 4. 检查内核日志中的摄像头信息
echo -e "${GREEN}[4] 内核日志中的摄像头信息${NC}"
if dmesg 2>/dev/null | grep -i "uvc\|video\|real sense\|realsense" | tail -20; then
    echo ""
else
    echo -e "${YELLOW}内核日志中无摄像头相关信息${NC}"
fi
echo ""

# 5. 检查用户权限
echo -e "${GREEN}[5] 用户组权限${NC}"
if groups | grep -q video; then
    echo -e "${GREEN}✓ 当前用户在 video 组中${NC}"
else
    echo -e "${RED}✗ 当前用户不在 video 组中${NC}"
    echo -e "${YELLOW}解决方法: sudo useradd -aG video $USER${NC}"
fi
echo ""

# 6. 测试摄像头访问
echo -e "${GREEN}[6] 测试摄像头访问${NC}"
for i in {0..4}; do
    if [ -e "/dev/video$i" ]; then
        echo -e "测试 /dev/video$i:"
        if timeout 2 v4l2-ctl --device=/dev/video$i --info >/dev/null 2>&1; then
            echo -e "  ${GREEN}✓ 可以访问${NC}"
        else
            echo -e "  ${RED}✗ 无法访问${NC}"
        fi
        break
    fi
done
echo ""

# 7. 建议
echo -e "${GREEN}[7] 排查建议${NC}"
echo -e "如果摄像头未检测到，请尝试："
echo -e "  1. 重新插拔 USB 连接"
echo -e "  2. 尝试不同的 USB 端口（USB 2.0/3.0）"
echo -e "  3. 检查摄像头是否在其他系统上工作"
echo -e "  4. 对于 RealSense: sudo apt-get install librealsense2-utils"
echo -e "  5. 检查 BIOS 中的摄像头设置"
echo ""
echo -e "${BLUE}========================================${NC}"
