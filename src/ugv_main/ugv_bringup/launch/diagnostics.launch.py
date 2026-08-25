"""diagnostics.launch.py — TF tree diagnostics and field-debugging tools.

Launches tools that help verify the GPS/EKF TF tree is healthy:
  - tf2_tools view_frames (generates /tmp/frames.pdf of the full TF tree)
  - EKF nodes with print_diagnostics: true (echo /diagnostics for detail)
  - RViz2 with the standard bringup view (optional, use_rviz:=true)

Usage
-----
  # Basic TF tree snapshot (view_frames only):
  ros2 launch ugv_bringup diagnostics.launch.py

  # Full diagnostics including RViz:
  ros2 launch ugv_bringup diagnostics.launch.py use_rviz:=true

  # With GPS enabled for global TF chain verification:
  ros2 launch ugv_bringup diagnostics.launch.py use_rviz:=true use_gps:=true

Prerequisites
-------------
  The main localization stack (bringup_imu_ekf.launch.py) must already be
  running in a separate terminal when you launch this file.

Output
------
  /tmp/frames.pdf  — PDF of the complete TF tree (open with any PDF viewer)
  /diagnostics     — Robot-localization EKF diagnostics (echo with rqt or CLI)
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, LogInfo
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='false',
        description='Launch RViz2 with the bringup view for TF tree visualisation.'
    )

    bringup_pkg = get_package_share_directory('ugv_bringup')
    rviz_config = os.path.join(bringup_pkg, 'rviz', 'view_bringup.rviz')

    # --- tf2_tools view_frames ---
    # Captures a one-shot snapshot of the TF tree and writes frames.pdf to /tmp.
    # Run this first to confirm map → odom → base_footprint is intact.
    view_frames = ExecuteProcess(
        cmd=['ros2', 'run', 'tf2_tools', 'view_frames',
             '--ros-args', '-p', 'output_dir:=/tmp'],
        output='screen',
    )

    log_frames = LogInfo(
        msg='[diagnostics] TF tree snapshot requested. '
            'Output will be written to /tmp/frames.pdf'
    )

    # --- Optional RViz2 ---
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_rviz')),
        arguments=['-d', rviz_config],
    )

    log_rviz_hint = LogInfo(
        msg='[diagnostics] To open RViz2 for TF tree display: '
            'ros2 launch ugv_bringup diagnostics.launch.py use_rviz:=true'
    )

    # --- Quick-reference CLI commands printed to terminal ---
    log_cli_hints = LogInfo(
        msg=(
            '\n'
            '=== Field Diagnostics Quick Reference ===\n'
            '# 1. Verify TF tree (map->odom->base_footprint chain):\n'
            '     ros2 run tf2_ros tf2_echo map odom\n'
            '     ros2 run tf2_ros tf2_echo odom base_footprint\n'
            '\n'
            '# 2. Check GPS fix quality:\n'
            '     ros2 topic echo /gps/fix --once\n'
            '     # Expect status.status >= 0, position_covariance[0] < 4.0\n'
            '\n'
            '# 3. Monitor GPS-derived odometry:\n'
            '     ros2 topic echo /odometry/gps\n'
            '\n'
            '# 4. Monitor global fused odometry:\n'
            '     ros2 topic echo /odometry/global\n'
            '\n'
            '# 5. Check EKF diagnostics:\n'
            '     ros2 topic echo /diagnostics\n'
            '\n'
            '# 6. Optional fixed-datum workflow (not required for normal GPS startup):\n'
            '     ros2 run ugv_bringup set_datum --list\n'
            '     ros2 run ugv_bringup set_datum --lat 52.3676 --lon 4.9041\n'
            '========================================='
        )
    )

    return LaunchDescription([
        use_rviz_arg,
        log_frames,
        log_cli_hints,
        log_rviz_hint,
        view_frames,
        rviz_node,
    ])
