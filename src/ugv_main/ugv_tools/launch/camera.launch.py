from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='usb_cam',
            executable='usb_cam_node_exe',
            name='usb_cam',
            parameters=[{
                'video_device': '/dev/video0',
                'image_width': 320,
                'image_height': 240,
                'framerate': 20.0,
                'pixel_format': 'mjpeg2rgb'
            }]
        )
    ])
