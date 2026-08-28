from launch import LaunchDescription
from launch_ros.actions import Node
import os
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration, PythonExpression

# Function to generate launch description
def generate_launch_description():

    # Declare launch argument for whether to launch RViz2
    use_rviz_arg = DeclareLaunchArgument('use_rviz', default_value='false',
                                     description='Whether to launch RViz2')

    # Declare machine role argument
    machine_arg = DeclareLaunchArgument('machine', default_value='rpi',
                                      description='Machine role: rpi (robot) or laptop (nav). Controls TF publishing authority.')
                                     
    # Include launch description for bringup_lidar.launch.py (conditional - when on robot)
    bringup_lidar_launch = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        [os.path.join(get_package_share_directory('ugv_bringup'), 'launch'),
         '/bringup_lidar.launch.py']),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'rviz_config': 'slam_2d',
            'machine': LaunchConfiguration('machine'),
        }.items(),
        condition=IfCondition(PythonExpression(["'", LaunchConfiguration('machine'), "' == 'rpi'"]))
    )
    
    # Include display.launch.py when NOT using lidar (laptop mode - for RViz and robot state)
    display_launch = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        [os.path.join(get_package_share_directory('ugv_description'), 'launch'),
         '/display.launch.py']),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'rviz_config': 'slam_2d',
            'namespace': '',
        }.items(),
        condition=UnlessCondition(PythonExpression(["'", LaunchConfiguration('machine'), "' == 'rpi'"]))
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
        machine_arg,
        bringup_lidar_launch,
        display_launch,
        robot_pose_publisher_launch,
        gmapping_launch
    ])
