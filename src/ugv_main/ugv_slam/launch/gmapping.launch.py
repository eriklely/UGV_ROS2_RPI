from launch import LaunchDescription
from launch_ros.actions import Node
import os
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.conditions import IfCondition
from launch.actions import DeclareLaunchArgument
from launch.substitutions import Command, LaunchConfiguration, PythonExpression

# Function to generate launch description
def generate_launch_description():

    # Declare launch argument for whether to launch RViz2
    use_rviz_arg = DeclareLaunchArgument('use_rviz', default_value='false',
                                     description='Whether to launch RViz2')

    # Declare launch argument for standalone mode.
    # standalone=true (default): start bringup_lidar here (single-machine, all-in-one).
    # standalone=false: the RPi already provides odometry and lidar; do not start
    # bringup_lidar to avoid a duplicate /odom publisher conflict.
    standalone_arg = DeclareLaunchArgument(
        'standalone', default_value='true',
        description='true = single-machine mode (starts bringup_lidar). '
                    'false = desktop-only mode (RPi already provides /odom and lidar).'
    )

    # Declare launch argument for GPS mode.
    # GMapping builds a local occupancy-grid map and publishes map->odom TF.
    # Running it alongside the GPS/EKF global localization stack creates two
    # conflicting map->odom publishers.  Set use_gps:=true only to acknowledge
    # this; a warning is printed and gmapping is still launched, but operators
    # must ensure only one map->odom source is active at a time.
    use_gps_arg = DeclareLaunchArgument(
        'use_gps', default_value='false',
        description='GPS mode acknowledgement flag. '
                    'GMapping and GPS-based global localization both publish map->odom '
                    'and will conflict. Do not use both simultaneously.'
    )

    # Warn when GPS mode is flagged: GMapping and GPS/EKF both try to publish
    # the map->odom transform, which causes TF tree conflicts.
    log_gps_conflict = LogInfo(
        condition=IfCondition(LaunchConfiguration('use_gps')),
        msg='[gmapping] WARNING: use_gps:=true detected. '
            'GMapping publishes map->odom TF, which conflicts with the GPS/EKF '
            'global localization stack. Do not run both simultaneously.'
    )

    # Include launch description for bringup_lidar.launch.py only in standalone mode.
    # When standalone:=false the RPi already provides odometry and lidar; starting
    # bringup_lidar here would create a second /odom publisher and conflict.
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

    # Include launch description for mapping.launch.py
    gmapping_launch = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        [os.path.join(get_package_share_directory('slam_gmapping'), 'launch'),
         '/mapping.launch.py'])
    )  

    # Include launch description for robot_pose_publisher_launch.py
    robot_pose_publisher_launch = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        [os.path.join(get_package_share_directory('robot_pose_publisher'), 'launch'),
         '/robot_pose_publisher_launch.py'])
    ) 
        
    # Return launch description
    return LaunchDescription([
        use_rviz_arg,
        standalone_arg,
        use_gps_arg,
        log_gps_conflict,
        bringup_lidar_launch,
        rviz_node,
        robot_pose_publisher_launch,
        gmapping_launch
    ])
