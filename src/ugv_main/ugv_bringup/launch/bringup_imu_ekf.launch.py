from ament_index_python.packages import get_package_share_path
from launch_ros.substitutions import FindPackageShare
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
import os
from ament_index_python.packages import get_package_share_directory

from launch.actions import IncludeLaunchDescription, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    # Declare launch arguments
    pub_odom_tf_arg = DeclareLaunchArgument('pub_odom_tf', default_value='false',
                                            description='Whether to publish the tf from the original odom to the base_footprint')                                         
     
    use_rviz_arg = DeclareLaunchArgument('use_rviz', default_value='false',
                                         description='Whether to launch RViz2')  

    rviz_config_arg = DeclareLaunchArgument('rviz_config', default_value='bringup',
                                         description='Choose which rviz configuration to use')

    # GPS mode switch.  Pass use_gps:=true to enable navsat_transform_node and
    # the GPS-fusing EKF instance (map frame).  Defaults to false for GPS-free
    # local-only operation (odom frame only).
    use_gps_arg = DeclareLaunchArgument(
        'use_gps',
        default_value='false',
        description='Enable GPS/navsat_transform path for global localization. '
                    'When true, navsat_transform_node is started and a second EKF '
                    'instance fuses GPS odometry in the map frame. '
                    'When false, only local odom+IMU localization is active.'
    )

    bringup_pkg = get_package_share_directory('ugv_bringup')

    imu_filter_config = os.path.join(bringup_pkg, 'param', 'imu_filter_param.yaml')
    ekf_no_gps_config = os.path.join(bringup_pkg, 'param', 'ekf.yaml')
    ekf_gps_config = os.path.join(bringup_pkg, 'param', 'ekf_gps.yaml')
    navsat_config = os.path.join(bringup_pkg, 'param', 'navsat_transform_params.yaml')

    # Define the nodes to be launched                                     
    bringup_node = Node(
        package='ugv_bringup',
        executable='ugv_bringup',
    )
    # Include the robot state launch from the ugv_description package
    robot_state_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ugv_description'), 'launch', 'display.launch.py')
        ),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'rviz_config': LaunchConfiguration('rviz_config'),
        }.items()
    ) 
    # Define the nodes to be launched
    imu_complementary_filter_node = Node(
            package='imu_complementary_filter',
            executable='complementary_filter_node',
            name='complementary_filter_gain_node',
            output='screen',
            parameters=[
                {'do_bias_estimation': True},
                {'do_adaptive_gain': True},
                {'use_mag': False},
                {'gain_acc': 0.01},
                {'gain_mag': 0.01},
            ]
    )
    # Define the nodes to be launched
    imu_filter_node = Node(
        package='imu_filter_madgwick',
        executable='imu_filter_madgwick_node',
        parameters=[imu_filter_config]
    )
    # Define the nodes to be launched
    laser_bringup_launch = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        [os.path.join(get_package_share_directory('ldlidar'), 'launch'),
         '/ldlidar.launch.py'])
    )
    # Define the nodes to be launched
    driver_node = Node(
        package='ugv_bringup',
        executable='ugv_driver',
    )
    # Define the nodes to be launched
    base_node = Node(
        package='ugv_base_node',
        executable='base_node_ekf',
        parameters=[{'pub_odom_tf': LaunchConfiguration('pub_odom_tf')}]
    )

    # Local EKF (odom frame) — always active regardless of GPS mode.
    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node',
        output='screen',
        parameters=[ekf_no_gps_config],
        remappings=[('/odometry/filtered', '/odom')]
    )

    # --- GPS path (only started when use_gps:=true) ---

    # Log the active mode so operators can confirm in the terminal.
    log_gps_enabled = LogInfo(
        condition=IfCondition(LaunchConfiguration('use_gps')),
        msg='[bringup_imu_ekf] GPS mode ENABLED — '
            'navsat_transform_node + map-frame EKF are active '
            '(map-frame EKF TF publish is disabled in ekf_gps.yaml; '
            'AMCL or GMapping remains sole owner of map->odom). '
            'Drive straight 2-3 m after launch to initialise heading (world-lock).'
    )
    log_gps_disabled = LogInfo(
        condition=UnlessCondition(LaunchConfiguration('use_gps')),
        msg='[bringup_imu_ekf] GPS mode DISABLED — '
            'running local odom+IMU only. No global position correction.'
    )

    # navsat_transform_node — converts GPS fix to odometry/gps using
    # use_odometry_yaw (moving-start heading init).
    navsat_transform_node = Node(
        package='robot_localization',
        executable='navsat_transform_node',
        name='navsat_transform_node',
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_gps')),
        parameters=[navsat_config],
        remappings=[
            ('imu', '/imu/data'),
            ('gps/fix', '/gps/fix'),
            ('odometry/filtered', '/odom'),
            ('odometry/gps', '/odometry/gps'),
        ]
    )

    # Global EKF (map frame) — fuses GPS-derived odometry to provide a
    # global fused odometry estimate only. TF publishing is disabled in
    # ekf_gps.yaml so AMCL (navigation) or GMapping (mapping) remains
    # sole owner of map->odom.
    ekf_node_map = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_filter_node_map',
        output='screen',
        condition=IfCondition(LaunchConfiguration('use_gps')),
        parameters=[ekf_gps_config],
        remappings=[('/odometry/filtered', '/odometry/global')]
    )

    return LaunchDescription([
        pub_odom_tf_arg,
        use_rviz_arg,
        rviz_config_arg,
        use_gps_arg,
        log_gps_enabled,
        log_gps_disabled,
        robot_state_launch,
        bringup_node,
        imu_complementary_filter_node,
        #imu_filter_node,
        laser_bringup_launch,
        driver_node,
        base_node,
        ekf_node,
        navsat_transform_node,
        ekf_node_map,
    ])

