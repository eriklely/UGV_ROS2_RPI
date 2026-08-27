#!/usr/bin/env python3

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([

        # Xbox controller driver (standardized axes)
        Node(
            package='joy',
            executable='game_controller_node',
            name='game_controller',
            namespace='ugv',
            output='screen',
            parameters=[{
                'device_id': 0,          # change if you have multiple controllers
                'deadzone': 0.15,
                'autorepeat_rate': 20.0,
            }]
        ),

        # Your teleop + camera node
        Node(
            package='ugv_tools',
            executable='joy_ctrl',
            name='joy_ctrl',
            namespace='ugv',
            output='screen',
            parameters=[{
                'xspeed_limit': 0.5,
                'angular_speed_limit': 5.0,
            }]
        ),
    ])
