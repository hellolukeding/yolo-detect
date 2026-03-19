#!/bin/bash
################################################################################
# 快速重启服务脚本
################################################################################

SERVICE_NAME="yolo-streaming"

echo "重启 YOLO 推流服务..."

# 重新检测摄像头
echo "1. 检测摄像头..."
sudo bash /opt/yolo-detect/deploy/scripts/detect_camera.sh

# 重启服务
echo "2. 重启服务..."
sudo systemctl restart $SERVICE_NAME

# 显示状态
echo "3. 服务状态:"
sudo systemctl status $SERVICE_NAME --no-pager

echo ""
echo "查看日志: sudo journalctl -u $SERVICE_NAME -f"
