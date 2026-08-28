import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.conditions import IfCondition, UnlessCondition


def generate_launch_description():
    machine_arg = DeclareLaunchArgument(
        'machine', default_value='rpi',
        description='Machine role: rpi (robot) or laptop (nav). Controls TF publishing authority.'
    )
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
            'machine': LaunchConfiguration('machine'),
        }.items()
    )

    navsat_transform_node = Node(
        package='robot_localization',
        executable='navsat_transform_node',
        name='navsat_transform_node',
        output='screen',
        parameters=[os.path.join(ugv_bringup_dir, 'param', 'navsat_transform_params.yaml')],
        remappings=[
            ('imu/data', 'imu/data'),
            ('odometry/filtered', 'odom'),
            ('gps/fix', 'gps/fix'),
            ('odometry/gps', 'odometry/gps'),
        ]
    )

    # FIX: publish_tf should be a boolean, use two nodes with IfCondition
    ekf_global_node_rpi = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node_global',
        output='screen',
        parameters=[os.path.join(ugv_bringup_dir, 'param', 'ekf_gps.yaml'), {'publish_tf': True}],
        remappings=[('odometry/filtered', 'odometry/global')],
        condition=IfCondition(PythonExpression(["'", LaunchConfiguration('machine'), "' == 'rpi'"]))
    )

    ekf_global_node_laptop = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node_global',
        output='screen',
        parameters=[os.path.join(ugv_bringup_dir, 'param', 'ekf_gps.yaml'), {'publish_tf': False}],
        remappings=[('odometry/filtered', 'odometry/global')],
        condition=UnlessCondition(PythonExpression(["'", LaunchConfiguration('machine'), "' == 'rpi'"]))
    )

    return LaunchDescription([
        machine_arg,
        use_rviz_arg,
        pub_odom_tf_arg,
        bringup_imu_ekf_launch,
        navsat_transform_node,
        ekf_global_node_rpi,
        ekf_global_node_laptop,
    ])

