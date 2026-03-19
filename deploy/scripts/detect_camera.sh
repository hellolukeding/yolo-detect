#!/bin/bash
################################################################################
# 摄像头检测脚本
# 自动检测并配置可用的摄像头（USB 摄像头 > 网络摄像头）
################################################################################

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

INSTALL_DIR="/opt/yolo-detect"
CONFIG_FILE="$INSTALL_DIR/deploy/config/service.conf"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}摄像头检测工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 检测 USB 摄像头
echo -e "${GREEN}[1/3] 检测 USB 摄像头...${NC}"

USB_CAMERAS=()
for i in {0..9}; do
    if [ -e "/dev/video$i" ]; then
        DEVICE_NAME=$(v4l2-ctl --device=/dev/video$i --info 2>/dev/null | grep "Card type" | cut -d: -f2 | xargs || echo "Unknown")
        USB_CAMERAS+=("/dev/video$i|$DEVICE_NAME")
        echo -e "  发现: ${YELLOW}/dev/video$i${NC} - $DEVICE_NAME"
    fi
done

if [ ${#USB_CAMERAS[@]} -eq 0 ]; then
    echo -e "  ${YELLOW}未找到 USB 摄像头${NC}"
else
    echo -e "  ${GREEN}共找到 ${#USB_CAMERAS[@]} 个 USB 摄像头${NC}"
fi

# 检测网络摄像头
echo ""
echo -e "${GREEN}[2/3] 检测网络摄像头...${NC}"

# 从配置文件读取 RTSP 地址
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
    if [ -n "$RTSP_URL" ]; then
        echo -e "  配置的 RTSP 地址: ${YELLOW}$RTSP_URL${NC}"

        # 测试连接
        if command -v ffprobe &> /dev/null; then
            if timeout 5 ffprobe -v error -show_entries stream=codec_type -of default=noprint_wrappers=1 "$RTSP_URL" 2>/dev/null | grep -q video; then
                echo -e "  ${GREEN}✓ 网络摄像头连接正常${NC}"
                RTSP_AVAILABLE=true
            else
                echo -e "  ${YELLOW}⚠ 网络摄像头无法连接${NC}"
                RTSP_AVAILABLE=false
            fi
        else
            echo -e "  ${YELLOW}⚠ 未安装 ffprobe，无法测试连接${NC}"
            RTSP_AVAILABLE=true
        fi
    else
        echo -e "  ${YELLOW}未配置 RTSP 地址${NC}"
        RTSP_AVAILABLE=false
    fi
else
    echo -e "  ${YELLOW}配置文件不存在: $CONFIG_FILE${NC}"
    RTSP_AVAILABLE=false
fi

# 选择摄像头
echo ""
echo -e "${GREEN}[3/3] 选择摄像头...${NC}"

SELECTED_CAMERA=""

# 优先使用网络摄像头
if [ "$RTSP_AVAILABLE" = true ]; then
    echo -e "  ${GREEN}使用网络摄像头: $RTSP_URL${NC}"
    SELECTED_CAMERA="$RTSP_URL"
    CAMERA_TYPE="rtsp"
elif [ ${#USB_CAMERAS[@]} -gt 0 ]; then
    # 使用第一个 USB 摄像头
    FIRST_CAMERA="${USB_CAMERAS[0]}"
    CAMERA_PATH=$(echo "$FIRST_CAMERA" | cut -d'|' -f1)
    CAMERA_NAME=$(echo "$FIRST_CAMERA" | cut -d'|' -f2)
    echo -e "  ${GREEN}使用 USB 摄像头: $CAMERA_PATH ($CAMERA_NAME)${NC}"
    SELECTED_CAMERA="$CAMERA_PATH"
    CAMERA_TYPE="usb"
else
    echo -e "  ${YELLOW}⚠ 未找到可用摄像头！${NC}"
    exit 1
fi

# 更新配置文件
echo ""
echo -e "${GREEN}更新配置文件...${NC}"

# 创建或更新配置文件
mkdir -p "$(dirname "$CONFIG_FILE")"
cat > "$CONFIG_FILE" << EOF
# YOLO 推流服务配置文件
# 自动生成于 $(date)

# 摄像头配置
CAMERA_TYPE=$CAMERA_TYPE
CAMERA_DEVICE="$SELECTED_CAMERA"
RTSP_URL="$RTSP_URL"

# 推流配置
PUSH_HOST=$PUSH_HOST
PUSH_PORT=$PUSH_PORT

# 检测配置
MODEL_PATH="$INSTALL_DIR/models/person_detector.pt"
CONFIDENCE=0.5
IOU=0.45
DEVICE="cpu"

# 视频配置
VIDEO_WIDTH=640
VIDEO_HEIGHT=480
FPS=15
BITRATE=500

# 日志配置
LOG_LEVEL="INFO"
LOG_DIR="$INSTALL_DIR/logs"
EOF

echo -e "  ${GREEN}配置已保存: $CONFIG_FILE${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}摄像头配置完成${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "当前摄像头: ${YELLOW}$SELECTED_CAMERA${NC}"
echo -e "类型: ${YELLOW}$CAMERA_TYPE${NC}"
echo ""
