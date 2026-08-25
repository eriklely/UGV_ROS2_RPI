import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz', default_value='false',
        description='Whether to launch RViz2'
    )
    pub_odom_tf_arg = DeclareLaunchArgument(
        'pub_odom_tf', default_value='false',
        description='Whether to publish the tf from the original odom to the base_footprint'
    )

    ugv_bringup_dir = get_package_share_directory('ugv_bringup')

    bringup_imu_ekf_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ugv_bringup_dir, 'launch', 'bringup_imu_ekf.launch.py')
        ),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'pub_odom_tf': LaunchConfiguration('pub_odom_tf'),
        }.items()
    )

    navsat_transform_node = Node(
        package='robot_localization',
        executable='navsat_transform_node',
        name='navsat_transform_node',
        output='screen',
        parameters=[os.path.join(ugv_bringup_dir, 'param', 'navsat_transform_params.yaml')],
        remappings=[
            ('imu/data', '/imu/data'),
            ('odometry/filtered', '/odom'),
            ('gps/fix', '/gps/fix'),
            ('odometry/gps', '/odometry/gps'),
        ]
    )

    ekf_global_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node_global',
        output='screen',
        parameters=[os.path.join(ugv_bringup_dir, 'param', 'ekf_gps.yaml')],
        remappings=[('/odometry/filtered', '/odometry/global')]
    )

    return LaunchDescription([
        use_rviz_arg,
        pub_odom_tf_arg,
        bringup_imu_ekf_launch,
        navsat_transform_node,
        ekf_global_node,
    ])
