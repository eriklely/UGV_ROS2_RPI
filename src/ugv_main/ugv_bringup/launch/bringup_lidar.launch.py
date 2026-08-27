import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PythonExpression
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    machine_arg = DeclareLaunchArgument(
        'machine', default_value='rpi',
        description='Machine role: rpi (robot) or laptop (nav). Controls TF publishing authority.'
    )
    use_ekf_odom_arg = DeclareLaunchArgument(
        'use_ekf_odom', default_value='false',
        description='If true, external EKF publishes odom->base_footprint; base_node should not publish TF'
    )
    pub_odom_tf_arg = DeclareLaunchArgument(
        'pub_odom_tf',
        default_value=PythonExpression(["'true' if '", LaunchConfiguration('machine'), "' == 'rpi' and '", LaunchConfiguration('use_ekf_odom'), "' == 'false' else 'false'"]),
        description='Whether to publish the tf from the original odom to the base_footprint. Auto-disabled on laptop or when EKF is active.'
    )
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz', default_value='false',
        description='Whether to launch RViz2'
    )
    rviz_config_arg = DeclareLaunchArgument(
        'rviz_config', default_value='bringup',
        description='Choose which rviz configuration to use'
    )
    robot_state_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ugv_description'), 'launch', 'display.launch.py')
        ),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'rviz_config': LaunchConfiguration('rviz_config'),
        }.items()
    )
    bringup_node = Node(
        package='ugv_bringup',
        executable='ugv_bringup',
        namespace='ugv',
    )
    driver_node = Node(
        package='ugv_bringup',
        executable='ugv_driver',
        namespace='ugv',
    )
    laser_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ldlidar'), 'launch', 'ldlidar.launch.py')
        )
    )
    rf2o_laser_odometry_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('rf2o_laser_odometry'), 'launch', 'rf2o_laser_odometry.launch.py')
        )
    )
    base_node = Node(
        package='ugv_base_node',
        executable='base_node',
        namespace='ugv',
        parameters=[{'pub_odom_tf': LaunchConfiguration('pub_odom_tf')}]
    )
    return LaunchDescription([
        machine_arg,
        use_ekf_odom_arg,
        pub_odom_tf_arg,
        use_rviz_arg,
        rviz_config_arg,
        robot_state_launch,
        bringup_node,
        driver_node,
        laser_bringup_launch,
        rf2o_laser_odometry_launch,
        base_node
    ])
