#!/bin/bash
# ============================================================
# ugv_mode_launcher.sh
# Simplified unified menu launcher for UGV ROS2 modes
# Ubuntu 22.04 (Raspberry Pi / Laptop / Desktop)
#
# NOTE:
# - GPS/EKF bringup is separate from the Waveshare nav/slam launches.
# - If you want GPS/EKF odometry on the RPi instead of raw rf2o odometry,
#   run bringup_imu_ekf instead of bringup_lidar.
# - GPS aerial map can be used separately via Vizanti.
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAP_DIR="${SCRIPT_DIR}/src/ugv_main/ugv_nav/maps"

print_header() {
    clear
    echo -e "${CYAN}"
    echo "============================================================"
    echo "          UGV ROS2 Mode Launcher  (Ubuntu 22)"
    echo "============================================================"
    echo -e "${NC}"
}

# Auto-detect machine
detect_machine() {
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null || \
       { [ -f /proc/device-tree/model ] && grep -qi "raspberry" /proc/device-tree/model 2>/dev/null; }; then
        echo "rpi"
    else
        echo "laptop"
    fi
}

print_map_save_hints() {
    echo
    echo -e "${CYAN}>>> SECOND terminal (manual driving):${NC}"
    echo "    ros2 run ugv_tools keyboard_ctrl"
    echo
    echo -e "${CYAN}>>> When finished, save map:${NC}"
    echo "    cd ${MAP_DIR}"
    echo "    ros2 run nav2_map_server map_saver_cli -f ./map"
}

run_mode() {
    local title="$1"
    shift

    print_header
    echo -e "${GREEN}>>> ${title}${NC}"
    echo "Command: $*"
    "$@"
}

MACHINE=$(detect_machine)

print_header
echo -e "Detected machine: ${YELLOW}${MACHINE}${NC}"
echo
echo "1) Use detected type"
echo "2) Force RPI"
echo "3) Force Laptop / Desktop"
echo
read -rp "Select machine [1-3] (default 1): " mchoice
case $mchoice in
    2) MACHINE="rpi" ;;
    3) MACHINE="laptop" ;;
    *) ;;
esac

echo
echo -e "Running as: ${GREEN}${MACHINE}${NC}"
sleep 1

while true; do
    print_header
    echo -e "Machine: ${GREEN}${MACHINE}${NC}"
    echo
    echo -e "${BLUE}=== RPI MODES (run on Raspberry Pi) ===${NC}"
    echo "  1) Bringup Lidar only        (bringup_lidar)"
    echo "  2) Bringup IMU + EKF         (bringup_imu_ekf)"
    echo
    echo -e "${BLUE}=== LAPTOP MODES (run on laptop, RPi must be running bringup_imu_ekf) ===${NC}"
    echo "  3) Gmapping SLAM             (build a map)"
    echo "  4) Cartographer SLAM         (build a map)"
    echo "  5) Navigation AMCL/TEB       (navigate with saved map)"
    echo "  6) Navigation AMCL/DWA       (navigate with saved map)"
    echo
    echo -e "${BLUE}=== STANDALONE MODES (single machine, everything runs here) ===${NC}"
    echo "  7) Gmapping standalone"
    echo "  8) Cartographer standalone"
    echo "  9) Navigation standalone"
    echo
    echo "  Q) Quit"
    echo
    read -rp "Select mode: " choice

    case $choice in
        1)
            run_mode "Bringup Lidar only" \
                ros2 launch ugv_bringup bringup_lidar.launch.py use_rviz:=false
            ;;
        2)
            run_mode "Bringup IMU + EKF" \
                ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_rviz:=false
            ;;
        3)
            print_header
            echo -e "${GREEN}>>> Gmapping SLAM${NC}"
            echo "Command: ros2 launch ugv_slam gmapping.launch.py use_rviz:=true"
            print_map_save_hints
            echo
            ros2 launch ugv_slam gmapping.launch.py use_rviz:=true
            ;;
        4)
            print_header
            echo -e "${GREEN}>>> Cartographer SLAM${NC}"
            echo "Command: ros2 launch ugv_slam cartographer.launch.py use_rviz:=true"
            print_map_save_hints
            echo
            ros2 launch ugv_slam cartographer.launch.py use_rviz:=true
            ;;
        5)
            run_mode "Navigation AMCL/TEB" \
                ros2 launch ugv_nav nav.launch.py use_rviz:=true use_localization:=amcl use_localplan:=teb
            ;;
        6)
            run_mode "Navigation AMCL/DWA" \
                ros2 launch ugv_nav nav.launch.py use_rviz:=true use_localization:=amcl use_localplan:=dwa
            ;;
        7)
            print_header
            echo -e "${GREEN}>>> Gmapping standalone${NC}"
            echo "Command: ros2 launch ugv_slam gmapping.launch.py use_rviz:=true"
            print_map_save_hints
            echo
            ros2 launch ugv_slam gmapping.launch.py use_rviz:=true
            ;;
        8)
            print_header
            echo -e "${GREEN}>>> Cartographer standalone${NC}"
            echo "Command: ros2 launch ugv_slam cartographer.launch.py use_rviz:=true"
            print_map_save_hints
            echo
            ros2 launch ugv_slam cartographer.launch.py use_rviz:=true
            ;;
        9)
            run_mode "Navigation standalone" \
                ros2 launch ugv_nav nav.launch.py use_rviz:=true use_localization:=amcl use_localplan:=teb
            ;;
        Q|q)
            echo -e "${GREEN}Exiting. Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Try again.${NC}"
            sleep 1.5
            ;;
    esac

    echo
    echo -e "${YELLOW}Launch finished or interrupted.${NC}"
    read -rp "Press Enter to return to main menu..."
done
