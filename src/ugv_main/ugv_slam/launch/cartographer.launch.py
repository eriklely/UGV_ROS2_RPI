from launch import LaunchDescription
from launch_ros.actions import Node
import os
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression

def generate_launch_description():

    # Declare launch argument for whether to launch RViz2
    use_rviz_arg = DeclareLaunchArgument('use_rviz', default_value='false',
                                     description='Whether to launch RViz2')

    # standalone=true (default): start bringup_lidar here (single-machine, all-in-one).
    # standalone=false: the RPi already provides odometry and lidar over the network;
    # do not start bringup_lidar to avoid trying to open /dev/ttyUSB0 on the laptop.
    standalone_arg = DeclareLaunchArgument(
        'standalone', default_value='true',
        description='true = single-machine mode (starts bringup_lidar). '
                    'false = desktop-only mode (RPi already provides /odom and lidar).'
    )

    # Include launch description for bringing up the lidar — standalone mode only
    bringup_lidar_launch = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        [os.path.join(get_package_share_directory('ugv_bringup'), 'launch'),
         '/bringup_lidar.launch.py']),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'rviz_config': 'slam_2d',
        }.items(),
        condition=IfCondition(LaunchConfiguration('standalone'))
    )

    # In non-standalone mode, bringup_lidar is skipped so RViz must be launched
    # here directly when the user requests it.
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', os.path.join(get_package_share_directory('ugv_slam'), 'rviz', 'view_slam_2d.rviz')],
        condition=IfCondition(PythonExpression([
            "'", LaunchConfiguration('use_rviz'), "' == 'true'",
            " and '", LaunchConfiguration('standalone'), "' == 'false'"
        ]))
    )

    # Include launch description for robot pose publisher
    robot_pose_publisher_launch = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        [os.path.join(get_package_share_directory('robot_pose_publisher'), 'launch'),
         '/robot_pose_publisher_launch.py'])
    )

    # Include launch description for cartographer
    cartographer_launch = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        [os.path.join(get_package_share_directory('cartographer'), 'launch'),
         '/mapping.launch.py'])
    )

    # Return launch description
    return LaunchDescription([
        use_rviz_arg,
        standalone_arg,
        bringup_lidar_launch,
        rviz_node,
        robot_pose_publisher_launch,
        cartographer_launch
    ])
