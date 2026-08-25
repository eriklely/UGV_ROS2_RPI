#!/usr/bin/env bash
# set_gps_datum.sh — Set the navsat_transform_node datum via a ROS 2 service call.
#
# Usage
# -----
#   bash set_gps_datum.sh <latitude> <longitude> [altitude]
#
# Arguments
#   latitude   Decimal degrees (e.g. 52.06298566666667)
#   longitude  Decimal degrees (e.g. 5.114725833333333)
#   altitude   Metres above WGS-84 ellipsoid (default: 0.0)
#
# Examples
#   bash set_gps_datum.sh 52.06298566666667 5.114725833333333 2.3
#   bash set_gps_datum.sh 52.06298566666667 5.114725833333333
#
# Alternatively use the Python helper (registered as a ROS 2 executable):
#   ros2 run ugv_bringup set_datum --lat 52.06298566666667 \
#                                  --lon 5.114725833333333 \
#                                  --alt 2.3
#
# Prerequisite
# ------------
# The localization stack must be running before calling this script:
#   ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=true
#
# After a successful call, verify with:
#   ros2 topic echo /odometry/gps --once
# Expected output:
#   frame_id: map          # correct
#   child_frame_id: odom   # correct
#   position: small values near (0, 0)

set -euo pipefail

LAT="${1:-}"
LON="${2:-}"
ALT="${3:-0.0}"

if [[ -z "$LAT" || -z "$LON" ]]; then
    echo "Usage: bash set_gps_datum.sh <latitude> <longitude> [altitude]" >&2
    echo "Example: bash set_gps_datum.sh 52.06298566666667 5.114725833333333 2.3" >&2
    exit 1
fi

echo "Setting GPS datum: lat=${LAT}, lon=${LON}, alt=${ALT}"

ros2 service call /navsat_transform_node/set_datum \
    robot_localization/srv/SetDatum \
    "{latitude: ${LAT}, longitude: ${LON}, altitude: ${ALT}}"

echo ""
echo "Datum set. Verify with:"
echo "  ros2 topic echo /odometry/gps --once"
echo "Expected: frame_id: map, child_frame_id: odom, position near (0, 0)"
