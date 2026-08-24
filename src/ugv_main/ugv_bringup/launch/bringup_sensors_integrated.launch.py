import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pub_odom_tf_arg = DeclareLaunchArgument(
        'pub_odom_tf',
        default_value='true',
        description='Whether to publish the tf from odom to base_footprint',
    )

    gps_port_arg = DeclareLaunchArgument(
        'gps_port',
        default_value='/dev/ttyUSB0',
        description='Serial device used by the GPS receiver',
    )

    gps_baud_arg = DeclareLaunchArgument(
        'gps_baud',
        default_value='9600',
        description='Serial baud rate used by the GPS receiver',
    )

    gps_frame_id_arg = DeclareLaunchArgument(
        'gps_frame_id',
        default_value='base_link',
        description='Frame id used for raw GPS fixes',
    )

    robot_state_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ugv_description'),
                'launch',
                'display.launch.py',
            )
        ),
        launch_arguments={
            'use_rviz': 'false',
            'rviz_config': 'bringup',
        }.items(),
    )

    laser_bringup_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ldlidar'),
                'launch',
                'ldlidar.launch.py',
            )
        )
    )

    bringup_node = Node(
        package='ugv_bringup',
        executable='ugv_bringup',
        remappings=[('imu/data_raw', 'imu/data')],
    )

    gps_node = Node(
        package='nmea_navsat_driver',
        executable='nmea_serial_driver',
        name='gps_driver',
        output='screen',
        parameters=[{
            'port': LaunchConfiguration('gps_port'),
            'baud': LaunchConfiguration('gps_baud'),
            'frame_id': LaunchConfiguration('gps_frame_id'),
        }],
        remappings=[('fix', '/gps/fix')],
    )

    driver_node = Node(
        package='ugv_bringup',
        executable='ugv_driver',
    )

    base_node = Node(
        package='ugv_base_node',
        executable='base_node_ekf',
        parameters=[{'pub_odom_tf': LaunchConfiguration('pub_odom_tf')}],
    )

    return LaunchDescription([
        pub_odom_tf_arg,
        gps_port_arg,
        gps_baud_arg,
        gps_frame_id_arg,
        robot_state_launch,
        bringup_node,
        gps_node,
        laser_bringup_launch,
        driver_node,
        base_node,
    ])
