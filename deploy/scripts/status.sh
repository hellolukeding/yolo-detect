#!/bin/bash
################################################################################
# 服务状态检查脚本
################################################################################

SERVICE_NAME="yolo-streaming"
INSTALL_DIR="/opt/yolo-detect"

echo -e "\033[0;32m========================================\033[0m"
echo -e "\033[0;32mYOLO 推流服务 - 状态检查\033[0m"
echo -e "\033[0;32m========================================\033[0m"
echo ""

# 1. 服务状态
echo -e "\033[1;33m[1] 系统服务状态\033[0m"
if systemctl is-active --quiet $SERVICE_NAME; then
    echo -e "  状态: \033[0;32m运行中 ✓\033[0m"
    echo -e "  开机自启: $(systemctl is-enabled $SERVICE_NAME)"
else
    echo -e "  状态: \033[0;31m已停止 ✗\033[0m"
fi
echo ""

# 2. 摄像头状态
echo -e "\033[1;33m[2] 摄像头状态\033[0m"
if [ -f "$INSTALL_DIR/deploy/config/service.conf" ]; then
    source "$INSTALL_DIR/deploy/config/service.conf"
    echo -e "  类型: \033[0;36m$CAMERA_TYPE\033[0m"
    echo -e "  设备: \033[0;36m$CAMERA_DEVICE\033[0m"
else
    echo -e "  \033[0;31m配置文件不存在\033[0m"
fi

# USB 摄像头列表
echo -e "\n  USB 摄像头设备:"
for i in {0..4}; do
    if [ -e "/dev/video$i" ]; then
        NAME=$(v4l2-ctl --device=/dev/video$i --info 2>/dev/null | grep "Card type" | cut -d: -f2 | xargs || echo "Unknown")
        echo -e "    \033[0;32m✓\033[0m /dev/video$i - $NAME"
    fi
done
echo ""

# 3. 推流配置
echo -e "\033[1;33m[3] 推流配置\033[0m"
if [ -f "$INSTALL_DIR/deploy/config/service.conf" ]; then
    source "$INSTALL_DIR/deploy/config/service.conf"
    echo -e "  目标地址: \033[0;36m$PUSH_HOST:$PUSH_PORT\033[0m"
    echo -e "  模型预设: \033[0;36m${MODEL_PRESET:-standard}\033[0m"
    echo -e "  分辨率: \033[0;36m${VIDEO_WIDTH}x${VIDEO_HEIGHT}\033[0m"
    echo -e "  帧率: \033[0;36m${FPS} FPS\033[0m"
    echo -e "  比特率: \033[0;36m${BITRATE} kbps\033[0m"

    # 显示模型预设说明
    case "${MODEL_PRESET:-standard}" in
        full)
            echo -e "  功能: \033[0;32m行人+人脸+表情+年龄\033[0m"
            ;;
        standard)
            echo -e "  功能: \033[0;32m行人+人脸+表情\033[0m"
            ;;
        performance|minimal)
            echo -e "  功能: \033[0;33m仅行人检测\033[0m"
            ;;
    esac
fi
echo ""

# 4. 最近日志
echo -e "\033[1;33m[4] 最近日志 (最后10行)\033[0m"
if [ -f "$INSTALL_DIR/logs/streaming.log" ]; then
    tail -10 "$INSTALL_DIR/logs/streaming.log"
elif systemctl is-active --quiet $SERVICE_NAME; then
    journalctl -u $SERVICE_NAME -n 10 --no-pager
else
    echo -e "  \033[0;33m暂无日志\033[0m"
fi
echo ""

# 5. 资源使用
echo -e "\033[1;33m[5] 资源使用\033[0m"
if pgrep -f "start_service.py" > /dev/null; then
    PID=$(pgrep -f "start_service.py" | head -1)
    echo -e "  进程 ID: \033[0;36m$PID\033[0m"

    # 内存使用
    MEM=$(ps -p $PID -o rss= 2>/dev/null | awk '{printf "%.0f MB", $1/1024}')
    echo -e "  内存使用: \033[0;36m$MEM\033[0m"

    # CPU 使用
    CPU=$(ps -p $PID -o %cpu= 2>/dev/null | xargs)
    echo -e "  CPU 使用: \033[0;36m${CPU}%\033[0m"
else
    echo -e "  \033[0;31m进程未运行\033[0m"
fi
echo ""

echo -e "\033[0;32m========================================\033[0m"
echo -e "常用命令:"
echo -e "  启动: sudo systemctl start $SERVICE_NAME"
echo -e "  停止: sudo systemctl stop $SERVICE_NAME"
echo -e "  重启: sudo systemctl restart $SERVICE_NAME"
echo -e "  日志: sudo journalctl -u $SERVICE_NAME -f"
echo -e "  检测摄像头: sudo bash $INSTALL_DIR/deploy/scripts/detect_camera.sh"
echo -e "\033[0;32m========================================\033[0m"
