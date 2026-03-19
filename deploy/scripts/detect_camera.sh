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

# 检测视频设备
echo -e "${GREEN}[1/2] 检测 USB 视频设备...${NC}"

USB_CAMERAS=()
REALSENSE_FOUND=false
REALSENSE_DEVICE=""

for i in {0..9}; do
    if [ -e "/dev/video$i" ]; then
        # 尝试获取设备名称（多种方法）
        DEVICE_NAME=""

        # 方法1: 通过 v4l2-ctl 获取
        V4L_INFO=$(v4l2-ctl --device=/dev/video$i --info 2>/dev/null)
        if [ -n "$V4L_INFO" ]; then
            # 尝试提取 Card type
            CARD_TYPE=$(echo "$V4L_INFO" | grep -i "card type" | cut -d: -f2 | xargs)
            if [ -n "$CARD_TYPE" ]; then
                DEVICE_NAME="$CARD_TYPE"
            else
                # 尝试提取 Driver 后面的内容
                DRIVER_INFO=$(echo "$V4L_INFO" | grep -i "driver" | head -1)
                if [ -n "$DRIVER_INFO" ]; then
                    DEVICE_NAME=$(echo "$DRIVER_INFO" | sed 's/.*Driver //;s/ *$//')
                fi
            fi
        fi

        # 方法2: 如果 v4l2-ctl 无输出，检查是否是 RealSense
        if [ -z "$DEVICE_NAME" ]; then
            if lsusb 2>/dev/null | grep -qi "real sense\|realsense\|8086:0b3"; then
                DEVICE_NAME="Intel RealSense Depth Camera"
                REALSENSE_FOUND=true
            else
                DEVICE_NAME="USB Camera $i"
            fi
        fi

        # 添加到列表
        USB_CAMERAS+=("/dev/video$i|$DEVICE_NAME")
        echo -e "  发现: ${YELLOW}/dev/video$i${NC} - $DEVICE_NAME"
    fi
done

echo ""
if [ ${#USB_CAMERAS[@]} -eq 0 ]; then
    echo -e "${YELLOW}未找到 USB 摄像头${NC}"
else
    echo -e "${GREEN}共找到 ${#USB_CAMERAS[@]} 个视频设备${NC}"
fi

# 检测网络摄像头
echo ""
echo -e "${GREEN}[2/2] 检测网络摄像头...${NC}"

# 从配置文件读取 RTSP 地址（如果存在）
OLD_RTSP_URL=""
OLD_PUSH_HOST=""
OLD_PUSH_PORT=""

if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE" 2>/dev/null || true
    OLD_RTSP_URL="$RTSP_URL"
    OLD_PUSH_HOST="$PUSH_HOST"
    OLD_PUSH_PORT="$PUSH_PORT"
fi

RTSP_AVAILABLE=false
if [ -n "$OLD_RTSP_URL" ] && [ "$OLD_RTSP_URL" != '""' ]; then
    echo -e "  配置的 RTSP 地址: ${YELLOW}$OLD_RTSP_URL${NC}"

    # 测试连接
    if command -v ffprobe &> /dev/null; then
        if timeout 5 ffprobe -v error -show_entries stream=codec_type -of default=noprint_wrappers=1 "$OLD_RTSP_URL" 2>/dev/null | grep -q video; then
            echo -e "  ${GREEN}✓ 网络摄像头连接正常${NC}"
            RTSP_AVAILABLE=true
        else
            echo -e "  ${YELLOW}⚠ 网络摄像头无法连接${NC}"
        fi
    else
        RTSP_AVAILABLE=true
    fi
else
    echo -e "  ${YELLOW}未配置 RTSP 地址${NC}"
fi

# 选择摄像头
echo ""
echo -e "${GREEN}选择摄像头...${NC}"

SELECTED_CAMERA=""
CAMERA_TYPE=""

# 优先使用网络摄像头
if [ "$RTSP_AVAILABLE" = true ]; then
    echo -e "  ${GREEN}使用网络摄像头: $OLD_RTSP_URL${NC}"
    SELECTED_CAMERA="$OLD_RTSP_URL"
    CAMERA_TYPE="rtsp"
elif [ ${#USB_CAMERAS[@]} -gt 0 ]; then
    # 使用第一个 USB 摄像头
    FIRST_CAMERA="${USB_CAMERAS[0]}"
    CAMERA_PATH=$(echo "$FIRST_CAMERA" | cut -d'|' -f1)
    CAMERA_NAME=$(echo "$FIRST_CAMERA" | cut -d'|' -f2)

    # 从 /dev/video0 提取索引 0
    CAMERA_INDEX=$(echo "$CAMERA_PATH" | sed 's|/dev/video||')
    echo -e "  ${GREEN}使用 USB 摄像头: $CAMERA_PATH ($CAMERA_NAME)${NC}"
    SELECTED_CAMERA="$CAMERA_INDEX"
    CAMERA_TYPE="usb"
else
    echo -e "  ${YELLOW}⚠ 未找到可用摄像头！${NC}"
    exit 1
fi

# 更新配置文件
echo ""
echo -e "${GREEN}更新配置文件...${NC}"

# 创建配置目录
mkdir -p "$(dirname "$CONFIG_FILE")"

# 保留推流配置（如果有）
PUSH_HOST_CONFIG="${OLD_PUSH_HOST:-115.120.237.79}"
PUSH_PORT_CONFIG="${OLD_PUSH_PORT:-5004}"

cat > "$CONFIG_FILE" << EOF
# YOLO 推流服务配置文件
# 自动生成

# 摄像头配置
CAMERA_TYPE=$CAMERA_TYPE
CAMERA_DEVICE="$SELECTED_CAMERA"
RTSP_URL="$OLD_RTSP_URL"

# 模型预设
MODEL_PRESET="standard"

# 推流配置
PUSH_HOST=$PUSH_HOST_CONFIG
PUSH_PORT=$PUSH_PORT_CONFIG

# 检测配置
MODEL_PATH="models/person_detector.pt"
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
LOG_DIR="/opt/yolo-detect/logs"
EOF

echo -e "  ${GREEN}配置已保存: $CONFIG_FILE${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}摄像头配置完成${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "当前摄像头: ${YELLOW}$SELECTED_CAMERA${NC}"
echo -e "类型: ${YELLOW}$CAMERA_TYPE${NC}"
echo -e "推流地址: ${YELLOW}$PUSH_HOST_CONFIG:$PUSH_PORT_CONFIG${NC}"
echo ""
