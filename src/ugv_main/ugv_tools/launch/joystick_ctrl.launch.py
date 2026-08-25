#!/usr/bin/env python3

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # Declare the connect argument (usb or bt)
    connect_arg = DeclareLaunchArgument(
        'connect',
        default_value='usb',
        description='Controller connection type: usb or bt'
    )

    return LaunchDescription([
        connect_arg,

        # Xbox controller driver (standardized axes)
        Node(
            package='joy',
            executable='game_controller_node',
            name='game_controller',
            output='screen',
            parameters=[{
                'device_id': 0,
                'deadzone': 0.15,
                'autorepeat_rate': 20.0,
            }]
        ),

        # Your teleop + camera node
        Node(
            package='ugv_tools',
            executable='joy_ctrl',
            name='joy_ctrl',
            output='screen',
            parameters=[{
                'xspeed_limit': 0.5,
                'angular_speed_limit': 5.0,
                'connect': LaunchConfiguration('connect'),   # ← this line is important
            }]
        ),
    ])
