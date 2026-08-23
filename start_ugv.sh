#!/bin/bash

source /opt/ros/humble/setup.bash
source /home/ws/ugv_ws/install/setup.bash

export ROS_DOMAIN_ID=30
export UGV_MODEL=ugv_rover
export LDLIDAR_MODEL=ld19

# Fix serial permissions
chmod 666 /dev/ttyAMA0 /dev/serial0 /dev/ttyUSB0 /dev/ttyS0 2>/dev/null

echo "=== Starting UGV Rover bringup ==="
exec ros2 launch ugv_bringup bringup_lidar.launch.py use_rviz:=false
