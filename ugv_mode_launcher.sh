#!/bin/bash
# ============================================================
# ugv_mode_launcher.sh
# Clean unified menu launcher for UGV ROS2 modes
# Ubuntu 22.04 (Raspberry Pi / Laptop / Desktop)
# ============================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

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
       [ -f /proc/device-tree/model ] && grep -qi "raspberry" /proc/device-tree/model 2>/dev/null; then
        echo "rpi"
    else
        echo "laptop"
    fi
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
    echo -e "${BLUE}=== RPI MODES ===${NC}"
    echo "  1) Bringup Lidar only     → ros2 launch ugv_bringup bringup_lidar.launch.py use_rviz:=false"
    echo "  2) Bringup IMU + EKF      → ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_rviz:=false"
    echo "     (NOTE: use option 2 instead of 1 if you want IMU/EKF fused odometry)"
    echo
    echo -e "${BLUE}=== LAPTOP / STANDALONE MODES ===${NC}"
    echo "  3) Gmapping SLAM          → ros2 launch ugv_slam gmapping.launch.py use_rviz:=true"
    echo "  4) Cartographer SLAM      → ros2 launch ugv_slam cartographer.launch.py use_rviz:=true"
    echo "  5) Navigation AMCL/TEB    → ros2 launch ugv_nav nav.launch.py use_rviz:=true use_localization:=amcl use_localplan:=teb"
    echo "  6) Navigation AMCL/DWA    → ros2 launch ugv_nav nav.launch.py use_rviz:=true use_localization:=amcl use_localplan:=dwa"
    echo "  7) Navigation EMCL/TEB    → ros2 launch ugv_nav nav.launch.py use_rviz:=true use_localization:=emcl use_localplan:=teb"
    echo "  8) RTABMAP RGB-D          → ros2 launch ugv_slam rtabmap_rgbd.launch.py use_rviz:=true"
    echo
    echo -e "${BLUE}=== GPS MODES (GPS input: /gps/fix from iPhone) ===${NC}"
    echo "  9) GPS EKF Bringup  [RUN ON RPI]    → ros2 launch ugv_bringup bringup_gps_ekf.launch.py use_rviz:=false"
    echo " 10) GPS Nav + Waypoints [RUN ON LAPTOP] → ros2 launch ugv_nav nav_gps_waypoints.launch.py use_rviz:=true"
    echo
    echo -e "${CYAN}GPS/Vizanti note:${NC} GPS remains available separately. For aerial map use, run Vizanti independently"
    echo "(it reads /gps/fix directly; no nav/slam integration needed)."
    echo
    echo "  Q) Quit"
    echo
    read -rp "Select mode: " choice

    case $choice in
        1)
            print_header
            echo -e "${GREEN}>>> Bringup Lidar only${NC}"
            echo "Command: ros2 launch ugv_bringup bringup_lidar.launch.py use_rviz:=false"
            ros2 launch ugv_bringup bringup_lidar.launch.py use_rviz:=false
            ;;
        2)
            print_header
            echo -e "${GREEN}>>> Bringup IMU + EKF${NC}"
            echo "Command: ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_rviz:=false"
            ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_rviz:=false
            ;;
        3)
            print_header
            echo -e "${GREEN}>>> Gmapping SLAM${NC}"
            echo "Command: ros2 launch ugv_slam gmapping.launch.py use_rviz:=true"
            echo
            echo -e "${CYAN}>>> SECOND terminal (manual driving):${NC}"
            echo "    ros2 run ugv_tools keyboard_ctrl"
            echo
            echo -e "${CYAN}>>> When finished, save map:${NC}"
            echo "    cd /home/ws/ugv_ws/src/ugv_main/ugv_nav/maps"
            echo "    ros2 run nav2_map_server map_saver_cli -f ./map"
            echo
            ros2 launch ugv_slam gmapping.launch.py use_rviz:=true
            ;;
        4)
            print_header
            echo -e "${GREEN}>>> Cartographer SLAM${NC}"
            echo "Command: ros2 launch ugv_slam cartographer.launch.py use_rviz:=true"
            echo
            echo -e "${CYAN}>>> SECOND terminal (manual driving):${NC}"
            echo "    ros2 run ugv_tools keyboard_ctrl"
            echo
            echo -e "${CYAN}>>> When finished, save map:${NC}"
            echo "    ros2 run nav2_map_server map_saver_cli -f ./map"
            echo
            ros2 launch ugv_slam cartographer.launch.py use_rviz:=true
            ;;
        5)
            print_header
            echo -e "${GREEN}>>> Navigation AMCL/TEB${NC}"
            echo "Command: ros2 launch ugv_nav nav.launch.py use_rviz:=true use_localization:=amcl use_localplan:=teb"
            ros2 launch ugv_nav nav.launch.py use_rviz:=true use_localization:=amcl use_localplan:=teb
            ;;
        6)
            print_header
            echo -e "${GREEN}>>> Navigation AMCL/DWA${NC}"
            echo "Command: ros2 launch ugv_nav nav.launch.py use_rviz:=true use_localization:=amcl use_localplan:=dwa"
            ros2 launch ugv_nav nav.launch.py use_rviz:=true use_localization:=amcl use_localplan:=dwa
            ;;
        7)
            print_header
            echo -e "${GREEN}>>> Navigation EMCL/TEB${NC}"
            echo "Command: ros2 launch ugv_nav nav.launch.py use_rviz:=true use_localization:=emcl use_localplan:=teb"
            ros2 launch ugv_nav nav.launch.py use_rviz:=true use_localization:=emcl use_localplan:=teb
            ;;
        8)
            print_header
            echo -e "${GREEN}>>> RTABMAP RGB-D${NC}"
            echo "Command: ros2 launch ugv_slam rtabmap_rgbd.launch.py use_rviz:=true"
            ros2 launch ugv_slam rtabmap_rgbd.launch.py use_rviz:=true
            ;;
        9)
            print_header
            echo -e "${GREEN}>>> GPS EKF Bringup  [RUN ON RPI]${NC}"
            echo "Command: ros2 launch ugv_bringup bringup_gps_ekf.launch.py use_rviz:=false"
            echo
            echo -e "${CYAN}GPS input: /gps/fix (iPhone)${NC}"
            echo -e "${CYAN}Starts: hardware bringup + navsat_transform + dual EKF (local + global)${NC}"
            echo -e "${CYAN}Outputs: /odometry/global and map→odom TF for Nav2 on laptop${NC}"
            echo
            ros2 launch ugv_bringup bringup_gps_ekf.launch.py use_rviz:=false
            ;;
        10)
            print_header
            echo -e "${GREEN}>>> GPS Nav + Waypoints  [RUN ON LAPTOP]${NC}"
            echo "Command: ros2 launch ugv_nav nav_gps_waypoints.launch.py use_rviz:=true"
            echo
            echo -e "${CYAN}GPS input: /gps/fix (iPhone) — make sure mode 9 is running on RPi first${NC}"
            echo -e "${CYAN}Starts: Nav2 (AMCL/TEB) + RViz + GPS waypoint follower${NC}"
            echo -e "${CYAN}Edit waypoints: src/ugv_main/ugv_nav/config/gps_waypoints_example.yaml${NC}"
            echo
            ros2 launch ugv_nav nav_gps_waypoints.launch.py use_rviz:=true
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
