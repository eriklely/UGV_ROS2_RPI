from ament_index_python.packages import get_package_share_path
from launch_ros.substitutions import FindPackageShare
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration, PythonExpression

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import os
from ament_index_python.packages import get_package_share_directory

from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    machine_arg = DeclareLaunchArgument(
        'machine', default_value='rpi',
        description='Machine role: rpi (robot) or laptop (nav). Controls TF publishing authority.'
    )
    pub_odom_tf_arg = DeclareLaunchArgument('pub_odom_tf', default_value='false',
                                            description='Whether to publish the tf from the original odom to the base_footprint')
    use_rviz_arg = DeclareLaunchArgument('use_rviz', default_value='false',
                                         description='Whether to launch RViz2')
    rviz_config_arg = DeclareLaunchArgument('rviz_config', default_value='bringup',
                                            description='Choose which rviz configuration to use')
    use_lidar_odom_arg = DeclareLaunchArgument('use_lidar_odom', default_value='true',
                                               description='Fuse lidar odometry (rf2o) into EKF for slip resilience')
    imu_filter_config = os.path.join(
        get_package_share_directory('ugv_bringup'),
        'param',
        'imu_filter_param.yaml'
    )
    bringup_node = Node(
        package='ugv_bringup',
        executable='ugv_bringup',
        namespace='ugv',
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
    imu_complementary_filter_node = Node(
            package='imu_complementary_filter',
            executable='complementary_filter_node',
            name='complementary_filter_gain_node',
            namespace='ugv',
            output='screen',
            parameters=[
                {'do_bias_estimation': True},
                {'do_adaptive_gain': True},
                {'use_mag': False},
                {'gain_acc': 0.01},
                {'gain_mag': 0.01},
            ]
    )
    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        namespace='ugv',
        parameters=[imu_filter_config]
    )
    laser_bringup_launch = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        [os.path.join(get_package_share_directory('ldlidar'), 'launch'),
         '/ldlidar.launch.py'])
    )
    
    # rf2o laser odometry - only when use_lidar_odom is true
    rf2o_laser_odometry_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('rf2o_laser_odometry'), 'launch', 'rf2o_laser_odometry.launch.py')
        ),
        condition=IfCondition(LaunchConfiguration('use_lidar_odom'))
    )
    
    driver_node = Node(
        package='ugv_bringup',
        executable='ugv_driver',
        namespace='ugv',
    )
    base_node = Node(
        package='ugv_base_node',
        executable='base_node_ekf',
        namespace='ugv',
        parameters=[{'pub_odom_tf': LaunchConfiguration('pub_odom_tf')}]
    )
    
    # EKF config selection based on lidar odom usage
    ekf_config_file = os.path.join(
        get_package_share_directory('ugv_bringup'), 'param',
        'ekf_with_lidar.yaml'
    )
    ekf_config_file_no_lidar = os.path.join(
        get_package_share_directory('ugv_bringup'), 'param',
        'ekf.yaml'
    )
    
    ekf_node_with_lidar = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        namespace='ugv',
        output='screen',
        parameters=[ekf_config_file, {'publish_tf': PythonExpression(["'true' if '", LaunchConfiguration('machine'), "' == 'rpi' else 'false'"])}],
        remappings=[('odometry/filtered', 'odom')],
        condition=IfCondition(LaunchConfiguration('use_lidar_odom'))
    )
    
    ekf_node_no_lidar = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        namespace='ugv',
        output='screen',
        parameters=[ekf_config_file_no_lidar, {'publish_tf': PythonExpression(["'true' if '", LaunchConfiguration('machine'), "' == 'rpi' else 'false'"])}],
        remappings=[('odometry/filtered', 'odom')],
        condition=UnlessCondition(LaunchConfiguration('use_lidar_odom'))
    )

    # Include bringup_lidar with machine argument passed through
    bringup_lidar_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ugv_bringup'), 'launch', 'bringup_lidar.launch.py')
        ),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'rviz_config': 'slam_2d',
            'machine': LaunchConfiguration('machine'),
            'use_ekf_odom': 'true',  # EKF is running, so base_node should not publish TF
        }.items()
    )

    return LaunchDescription([
        machine_arg,
        pub_odom_tf_arg,
        use_rviz_arg,
        rviz_config_arg,
        use_lidar_odom_arg,
        robot_state_launch,
        bringup_lidar_launch,
        imu_complementary_filter_node,
        #imu_filter_node,
        laser_bringup_launch,
        rf2o_laser_odometry_launch,
        driver_node,
        base_node,
        ekf_node_with_lidar,
        ekf_node_no_lidar
    ])
