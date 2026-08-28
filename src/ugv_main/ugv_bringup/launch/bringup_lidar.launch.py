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
    # FIX: Automatically set pub_odom_tf based on machine and use_ekf_odom
    # When NO EKF (use_ekf_odom=false) AND on RPi (machine=rpi), base_node must publish odom->base_footprint TF
    pub_odom_tf_auto = PythonExpression([
        "'", LaunchConfiguration('use_ekf_odom'), "' == 'false' and '", LaunchConfiguration('machine'), "' == 'rpi'"
    ])
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
        executable='base_node_ekf',
        namespace='ugv',
        parameters=[{'pub_odom_tf': pub_odom_tf_auto}]
    )
    return LaunchDescription([
        machine_arg,
        use_ekf_odom_arg,
        use_rviz_arg,
        rviz_config_arg,
        robot_state_launch,
        bringup_node,
        driver_node,
        laser_bringup_launch,
        rf2o_laser_odometry_launch,
        base_node
    ])

