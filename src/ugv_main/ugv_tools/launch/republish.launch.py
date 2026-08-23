from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        Node(
            package='image_transport',
            executable='republish',
            name='republish',
            arguments=['compressed', 'raw'],
            remappings=[
                ('in/compressed', '/image_raw/compressed'),
                ('out', '/image'),
            ],
            parameters=[{
                'compressed.jpeg_quality': 25,
            }],
            output='screen',
        )
    ])
