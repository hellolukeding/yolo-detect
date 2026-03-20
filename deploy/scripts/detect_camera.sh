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
OLD_SERVICE_ROLE="integrated"
OLD_RTSP_URL=""
OLD_PUSH_HOST=""
OLD_PUSH_PORT=""
OLD_LISTEN_HOST="0.0.0.0"
OLD_LISTEN_PORT="5004"
OLD_MODEL_PRESET="standard"
OLD_MODEL_PATH="models/person_detector.pt"
OLD_CONFIDENCE="0.5"
OLD_IOU="0.45"
OLD_DEVICE="cpu"
OLD_VIDEO_WIDTH="640"
OLD_VIDEO_HEIGHT="480"
OLD_FPS="15"
OLD_BITRATE="500"
OLD_LOG_LEVEL="INFO"
OLD_LOG_DIR="/opt/yolo-detect/logs"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}摄像头检测工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE" 2>/dev/null || true
    OLD_SERVICE_ROLE="${SERVICE_ROLE:-integrated}"
    OLD_RTSP_URL="${RTSP_URL:-}"
    OLD_PUSH_HOST="${PUSH_HOST:-115.120.237.79}"
    OLD_PUSH_PORT="${PUSH_PORT:-5004}"
    OLD_LISTEN_HOST="${LISTEN_HOST:-0.0.0.0}"
    OLD_LISTEN_PORT="${LISTEN_PORT:-5004}"
    OLD_MODEL_PRESET="${MODEL_PRESET:-standard}"
    OLD_MODEL_PATH="${MODEL_PATH:-models/person_detector.pt}"
    OLD_CONFIDENCE="${CONFIDENCE:-0.5}"
    OLD_IOU="${IOU:-0.45}"
    OLD_DEVICE="${DEVICE:-cpu}"
    OLD_VIDEO_WIDTH="${VIDEO_WIDTH:-640}"
    OLD_VIDEO_HEIGHT="${VIDEO_HEIGHT:-480}"
    OLD_FPS="${FPS:-15}"
    OLD_BITRATE="${BITRATE:-500}"
    OLD_LOG_LEVEL="${LOG_LEVEL:-INFO}"
    OLD_LOG_DIR="${LOG_DIR:-/opt/yolo-detect/logs}"
fi

if [ "$OLD_SERVICE_ROLE" = "server" ]; then
    echo -e "${YELLOW}当前配置为 server 角色，跳过摄像头检测${NC}"
    echo -e "监听地址: ${YELLOW}${OLD_LISTEN_HOST}:${OLD_LISTEN_PORT}${NC}"
    exit 0
fi

# 检测视频设备
echo -e "${GREEN}[1/2] 检测 USB 视频设备...${NC}"

USB_CAMERAS=()
REALSENSE_FOUND=false
REALSENSE_DEVICE=""

for i in {0..9}; do
    if [ -e "/dev/video$i" ]; then
        # 尝试获取设备名称（多种方法）
        DEVICE_NAME=""
        CAPTURE_CAPABLE=false

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

            DEVICE_CAPS=$(echo "$V4L_INFO" | awk '
                /Device Caps/ {in_device_caps=1; next}
                in_device_caps && /^[[:space:]]+[[:alnum:]]/ {print; next}
                in_device_caps {exit}
            ')

            if echo "$DEVICE_CAPS" | grep -qi "Video Capture"; then
                CAPTURE_CAPABLE=true
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

        if echo "$DEVICE_NAME" | grep -qi "real sense\|realsense"; then
            REALSENSE_FOUND=true
        fi

        # 添加到列表
        USB_CAMERAS+=("/dev/video$i|$DEVICE_NAME|$CAPTURE_CAPABLE")
        if [ "$CAPTURE_CAPABLE" = true ]; then
            echo -e "  发现: ${YELLOW}/dev/video$i${NC} - $DEVICE_NAME ${GREEN}[可采集]${NC}"
        else
            echo -e "  发现: ${YELLOW}/dev/video$i${NC} - $DEVICE_NAME ${YELLOW}[非采集节点/待确认]${NC}"
        fi
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
    # 优先使用具有 Video Capture 能力的节点，避免选到 RealSense/多节点设备的元数据节点
    CAPTURE_ENTRIES=()
    for camera in "${USB_CAMERAS[@]}"; do
        CAMERA_CAPABLE=$(echo "$camera" | cut -d'|' -f3)
        if [ "$CAMERA_CAPABLE" = true ]; then
            CAPTURE_ENTRIES+=("$camera")
        fi
    done

    SELECTED_ENTRY=""
    if [ ${#CAPTURE_ENTRIES[@]} -gt 0 ]; then
        if [ "$REALSENSE_FOUND" = true ]; then
            LAST_INDEX=$((${#CAPTURE_ENTRIES[@]} - 1))
            SELECTED_ENTRY="${CAPTURE_ENTRIES[$LAST_INDEX]}"
        else
            SELECTED_ENTRY="${CAPTURE_ENTRIES[0]}"
        fi
    fi

    if [ -z "$SELECTED_ENTRY" ]; then
        SELECTED_ENTRY="${USB_CAMERAS[0]}"
    fi

    CAMERA_PATH=$(echo "$SELECTED_ENTRY" | cut -d'|' -f1)
    CAMERA_NAME=$(echo "$SELECTED_ENTRY" | cut -d'|' -f2)

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

# 创建配置目录
mkdir -p "$(dirname "$CONFIG_FILE")"

cat > "$CONFIG_FILE" << EOF
# YOLO 推流服务配置文件
# 自动生成

# 部署角色
SERVICE_ROLE="$OLD_SERVICE_ROLE"

# 摄像头配置
CAMERA_TYPE=$CAMERA_TYPE
CAMERA_DEVICE="$SELECTED_CAMERA"
RTSP_URL="$OLD_RTSP_URL"

# 模型预设
MODEL_PRESET="$OLD_MODEL_PRESET"

# 推流配置
PUSH_HOST=$OLD_PUSH_HOST
PUSH_PORT=$OLD_PUSH_PORT

# 收流配置
LISTEN_HOST="$OLD_LISTEN_HOST"
LISTEN_PORT=$OLD_LISTEN_PORT

# 检测配置
MODEL_PATH="$OLD_MODEL_PATH"
CONFIDENCE=$OLD_CONFIDENCE
IOU=$OLD_IOU
DEVICE="$OLD_DEVICE"

# 视频配置
VIDEO_WIDTH=$OLD_VIDEO_WIDTH
VIDEO_HEIGHT=$OLD_VIDEO_HEIGHT
FPS=$OLD_FPS
BITRATE=$OLD_BITRATE

# 日志配置
LOG_LEVEL="$OLD_LOG_LEVEL"
LOG_DIR="$OLD_LOG_DIR"
EOF

echo -e "  ${GREEN}配置已保存: $CONFIG_FILE${NC}"
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}摄像头配置完成${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "当前摄像头: ${YELLOW}$SELECTED_CAMERA${NC}"
echo -e "服务角色: ${YELLOW}$OLD_SERVICE_ROLE${NC}"
echo -e "类型: ${YELLOW}$CAMERA_TYPE${NC}"
echo -e "推流地址: ${YELLOW}$OLD_PUSH_HOST:$OLD_PUSH_PORT${NC}"
echo ""
