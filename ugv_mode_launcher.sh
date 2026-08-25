#!/bin/bash
# ============================================================
# ugv_mode_launcher.sh
# Clean unified menu launcher for UGV ROS2 modes
# Ubuntu 22.04 (Raspberry Pi / Laptop / Desktop)
# Fixed: GPS Mode no longer starts AMCL
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

# ============================================================
# Main Menu
# ============================================================
while true; do
    print_header
    echo -e "Machine: ${GREEN}${MACHINE}${NC}"
    echo
    echo -e "${BLUE}=== 1. NAVIGATION ===${NC}"
    echo "  1A) GPS Mode          (Outdoor, No Pre-Made Map)  ← NO AMCL"
    echo "  1B) AMCL Mode         (Indoor, Pre-Mapped)"
    echo
    echo -e "${BLUE}=== 2. MAPPING (Gmapping) ===${NC}"
    echo "  2A) Gmapping WITHOUT GPS"
    echo "  2B) Gmapping WITH GPS"
    echo
    echo -e "${BLUE}=== 3. SLAM (Cartographer) ===${NC}"
    echo "  3A) Cartographer WITHOUT GPS"
    echo "  3B) Cartographer WITH GPS"
    echo
    echo -e "${BLUE}=== 4. RTABMAP (3D SLAM) ===${NC}"
    echo "  4A) RTABMAP WITHOUT GPS"
    echo
    echo "  Q) Quit"
    echo
    read -rp "Select mode: " choice

    case $choice in

        # --------------------------------------------------
        # 1A. GPS Mode  (NO AMCL)
        # --------------------------------------------------
        1A|1a)
            print_header
            echo -e "${GREEN}>>> GPS Mode (Outdoor, No Pre-Made Map) - NO AMCL${NC}"
            if [ "$MACHINE" = "rpi" ]; then
                echo -e "${YELLOW}RPI: Starting odometry + GPS EKF...${NC}"
                echo "Command: ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=true use_rviz:=false"
                echo
                ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=true use_rviz:=false
            else
                echo -e "${YELLOW}Laptop: Nav2 with GPS (NO AMCL)...${NC}"
                echo "Command: ros2 launch ugv_nav nav.launch.py standalone:=false use_gps:=true use_rviz:=true"
                echo
                ros2 launch ugv_nav nav.launch.py standalone:=false use_gps:=true use_rviz:=true
            fi
            ;;

        # --------------------------------------------------
        # 1B. AMCL Mode
        # --------------------------------------------------
        1B|1b)
            print_header
            echo -e "${GREEN}>>> AMCL Mode (Indoor, Pre-Mapped)${NC}"
            if [ "$MACHINE" = "rpi" ]; then
                echo -e "${YELLOW}RPI: Starting odometry (NO GPS)...${NC}"
                echo "Command: ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=false use_rviz:=false"
                echo
                ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=false use_rviz:=false
            else
                echo -e "${YELLOW}Laptop: Nav2 with AMCL (no GPS)...${NC}"
                echo "Command: ros2 launch ugv_nav nav.launch.py standalone:=false use_gps:=false use_localization:=amcl use_rviz:=true"
                echo
                ros2 launch ugv_nav nav.launch.py standalone:=false use_gps:=false use_localization:=amcl use_rviz:=true
            fi
            ;;

        # --------------------------------------------------
        # 2A. Gmapping WITHOUT GPS
        # --------------------------------------------------
        2A|2a)
            print_header
            echo -e "${GREEN}>>> Gmapping WITHOUT GPS${NC}"
            if [ "$MACHINE" = "rpi" ]; then
                echo -e "${YELLOW}RPI: Starting odometry (no GPS)...${NC}"
                echo "Command: ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=false use_rviz:=false"
                echo
                ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=false use_rviz:=false
            else
                echo -e "${YELLOW}Laptop: Starting Gmapping...${NC}"
                echo "Command: ros2 launch ugv_slam gmapping.launch.py standalone:=false use_rviz:=true"
                echo
                echo -e "${CYAN}>>> SECOND terminal (manual driving):${NC}"
                echo "    ros2 run ugv_tools keyboard_ctrl"
                echo
                echo -e "${CYAN}>>> When finished, save map:${NC}"
                echo "    cd /home/ws/ugv_ws/src/ugv_main/ugv_nav/maps"
                echo "    ros2 run nav2_map_server map_saver_cli -f ./map"
                echo
                ros2 launch ugv_slam gmapping.launch.py standalone:=false use_gps:=false use_rviz:=true
            fi
            ;;

        # --------------------------------------------------
        # 2B. Gmapping WITH GPS
        # --------------------------------------------------
        2B|2b)
            print_header
            echo -e "${GREEN}>>> Gmapping WITH GPS${NC}"
            if [ "$MACHINE" = "rpi" ]; then
                echo -e "${YELLOW}RPI: Starting odometry + GPS EKF...${NC}"
                echo "Command: ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=true use_rviz:=false"
                echo
                ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=true use_rviz:=false
            else
                echo -e "${YELLOW}Laptop: Gmapping + GPS...${NC}"
                echo "Command: ros2 launch ugv_slam gmapping.launch.py standalone:=false use_gps:=true use_rviz:=true"
                echo
                echo -e "${CYAN}>>> SECOND terminal (manual driving):${NC}"
                echo "    ros2 run ugv_tools keyboard_ctrl"
                echo
                ros2 launch ugv_slam gmapping.launch.py standalone:=false use_gps:=true use_rviz:=true
            fi
            ;;

        # --------------------------------------------------
        # 3A. Cartographer WITHOUT GPS
        # --------------------------------------------------
        3A|3a)
            print_header
            echo -e "${GREEN}>>> Cartographer WITHOUT GPS${NC}"
            if [ "$MACHINE" = "rpi" ]; then
                echo -e "${YELLOW}RPI: Starting odometry (no GPS)...${NC}"
                echo "Command: ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=false use_rviz:=false"
                echo
                ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=false use_rviz:=false
            else
                echo -e "${YELLOW}Laptop: Starting Cartographer...${NC}"
                echo "Command: ros2 launch ugv_slam cartographer.launch.py use_rviz:=true"
                echo
                echo -e "${CYAN}>>> SECOND terminal (manual driving):${NC}"
                echo "    ros2 run ugv_tools keyboard_ctrl"
                echo
                ros2 launch ugv_slam cartographer.launch.py standalone:=false use_gps:=false use_rviz:=true
            fi
            ;;

        # --------------------------------------------------
        # 3B. Cartographer WITH GPS
        # --------------------------------------------------
        3B|3b)
            print_header
            echo -e "${GREEN}>>> Cartographer WITH GPS${NC}"
            if [ "$MACHINE" = "rpi" ]; then
                echo -e "${YELLOW}RPI: Starting odometry + GPS EKF...${NC}"
                echo "Command: ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=true use_rviz:=false"
                echo
                ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=true use_rviz:=false
            else
                echo -e "${YELLOW}Laptop: Starting Cartographer + GPS...${NC}"
                echo "Command: ros2 launch ugv_slam cartographer.launch.py use_gps:=true use_rviz:=true"
                echo
                echo -e "${CYAN}>>> SECOND terminal (manual driving):${NC}"
                echo "    ros2 run ugv_tools keyboard_ctrl"
                echo
                ros2 launch ugv_slam cartographer.launch.py standalone:=false use_gps:=true use_rviz:=true
            fi
            ;;

        # --------------------------------------------------
        # 4A. RTABMAP WITHOUT GPS
        # --------------------------------------------------
        4A|4a)
            print_header
            echo -e "${GREEN}>>> RTABMAP WITHOUT GPS${NC}"
            if [ "$MACHINE" = "rpi" ]; then
                echo -e "${YELLOW}RPI: Starting odometry (no GPS)...${NC}"
                echo "Command: ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=false use_rviz:=false"
                echo
                ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=false use_rviz:=false
            else
                echo -e "${YELLOW}Laptop: Starting RTABMAP RGB-D...${NC}"
                echo "Command: ros2 launch ugv_slam rtabmap_rgbd.launch.py use_rviz:=true"
                echo
                ros2 launch ugv_slam rtabmap_rgbd.launch.py standalone:=false use_rviz:=true
            fi
            ;;

        # --------------------------------------------------
        # Quit
        # --------------------------------------------------
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
