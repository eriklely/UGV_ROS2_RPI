import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, ComposableNodeContainer
from launch_ros.descriptions import ComposableNode


def generate_launch_description():

    pkg_dir = get_package_share_directory('ugv_vision')
    param_file = os.path.join(pkg_dir, 'config', 'params.yaml')

    # Launch argument to enable/disable rectify (default = false)
    use_rectify_arg = DeclareLaunchArgument(
        'use_rectify',
        default_value='false',
        description='Whether to start the image_proc rectify node'
    )

    # Camera node
    camera_node = Node(
        package='usb_cam',
        executable='usb_cam_node_exe',
        name='usb_cam',
        parameters=[param_file],
        output='screen'
    )

    # Optional rectify node
    rectify_container = ComposableNodeContainer(
        condition=IfCondition(LaunchConfiguration('use_rectify')),
        name='image_proc_container',
        namespace='',                          # <-- required
        package='rclcpp_components',
        executable='component_container',
        composable_node_descriptions=[
            ComposableNode(
                package='image_proc',
                plugin='image_proc::RectifyNode',
                name='rectify_color_node',
                remappings=[
                    ('image', 'image_raw'),
                    ('image_rect', 'image_rect')
                ],
            )
        ],
        output='screen'
    )

    return LaunchDescription([
        use_rectify_arg,
        camera_node,
        rectify_container,
    ])
