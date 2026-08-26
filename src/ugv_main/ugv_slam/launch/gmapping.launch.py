from launch import LaunchDescription
from launch_ros.actions import Node
import os
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration

# Function to generate launch description
def generate_launch_description():

    # Declare launch argument for whether to launch RViz2
    use_rviz_arg = DeclareLaunchArgument('use_rviz', default_value='false',
                                     description='Whether to launch RViz2')

    # Declare launch argument for whether to bring up lidar locally (on robot)
    # On laptop, lidar data comes from robot over ROS2 network
    use_lidar_arg = DeclareLaunchArgument('use_lidar', default_value='true',
                                      description='Whether to start lidar driver locally (robot=true, laptop=false)')
                                     
    # Include launch description for bringup_lidar.launch.py (conditional)
    bringup_lidar_launch = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        [os.path.join(get_package_share_directory('ugv_bringup'), 'launch'),
         '/bringup_lidar.launch.py']),
        launch_arguments={
            'use_rviz': LaunchConfiguration('use_rviz'),
            'rviz_config': 'slam_2d',
        }.items(),
        condition=IfCondition(LaunchConfiguration('use_lidar'))
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
        use_lidar_arg,
        bringup_lidar_launch, 
        robot_pose_publisher_launch,
        gmapping_launch
    ])
