import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    ugv_nav_dir = get_package_share_directory('ugv_nav')

    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz', default_value='true',
        description='Whether to launch RViz2'
    )

    nav_gps_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ugv_nav_dir, 'launch', 'nav_gps.launch.py')
        ),
        launch_arguments={'use_rviz': LaunchConfiguration('use_rviz')}.items()
    )

    waypoints_file = os.path.join(ugv_nav_dir, 'config', 'gps_waypoints_example.yaml')

    gps_waypoint_follower_node = Node(
        package='ugv_nav',
        executable='gps_waypoint_follower',
        name='gps_waypoint_follower',
        output='screen',
        parameters=[{'waypoints_file': waypoints_file}]
    )

    return LaunchDescription([
        use_rviz_arg,
        nav_gps_launch,
        gps_waypoint_follower_node,
    ])
