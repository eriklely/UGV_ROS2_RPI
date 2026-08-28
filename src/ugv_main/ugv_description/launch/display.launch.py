import os
from launch import LaunchDescription
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition


def get_rviz_config_file(context):
    rviz_config = context.launch_configurations['rviz_config']

    ugv_description_dir = get_package_share_directory('ugv_description')
    ugv_bringup_dir = get_package_share_directory('ugv_bringup')
    ugv_slam_dir = get_package_share_directory('ugv_slam')
    ugv_nav_dir = get_package_share_directory('ugv_nav')

    rviz_description_config = os.path.join(ugv_description_dir, 'rviz', 'view_description.rviz')
    rviz_bringup_config = os.path.join(ugv_bringup_dir, 'rviz', 'view_bringup.rviz')
    rviz_slam_2d_config = os.path.join(ugv_slam_dir, 'rviz', 'view_slam_2d.rviz')
    rviz_slam_3d_config = os.path.join(ugv_slam_dir, 'rviz', 'view_slam_3d.rviz')
    rviz_nav_2d_config = os.path.join(ugv_nav_dir, 'rviz', 'view_nav_2d.rviz')
    rviz_nav_3d_config = os.path.join(ugv_nav_dir, 'rviz', 'view_nav_3d.rviz')

    config_map = {
        'description': rviz_description_config,
        'bringup': rviz_bringup_config,
        'slam_2d': rviz_slam_2d_config,
        'slam_3d': rviz_slam_3d_config,
        'nav_2d': rviz_nav_2d_config,
        'nav_3d': rviz_nav_3d_config
    }

    return config_map.get(rviz_config, rviz_description_config)


def launch_setup(context, *args, **kwargs):

    rviz_config = context.launch_configurations['rviz_config']
    UGV_MODEL = os.environ['UGV_MODEL']
    urdf_file_name = UGV_MODEL + '.urdf'
    urdf_model_path = os.path.join(
        get_package_share_directory('ugv_description'),
        'urdf',
        urdf_file_name)

    use_jsp_gui = 'true' if rviz_config == 'description' else 'false'
    use_jsp = 'true' if rviz_config == 'description' else 'false'

    namespace = context.launch_configurations.get('namespace', '')

    with open(urdf_model_path, 'r') as f:
        robot_desc = f.read()

    robot_state_publisher_params = {
        'package': 'robot_state_publisher',
        'executable': 'robot_state_publisher',
        'parameters': [{'robot_description': robot_desc}],
        'condition': IfCondition(LaunchConfiguration('publish_robot_state')),
    }
    joint_state_publisher_gui_params = {
        'package': 'joint_state_publisher_gui',
        'executable': 'joint_state_publisher_gui',
        'name': 'joint_state_publisher_gui',
        'parameters': [{'robot_description': robot_desc}],
        'condition': IfCondition(use_jsp_gui),
    }
    joint_state_publisher_params = {
        'package': 'joint_state_publisher',
        'executable': 'joint_state_publisher',
        'name': 'joint_state_publisher',
        'parameters': [{'robot_description': robot_desc}],
        'condition': IfCondition(use_jsp),
    }

    if namespace:
        robot_state_publisher_params['namespace'] = namespace
        joint_state_publisher_gui_params['namespace'] = namespace
        joint_state_publisher_params['namespace'] = namespace

    robot_state_publisher_node = Node(**robot_state_publisher_params)
    joint_state_publisher_gui_node = Node(**joint_state_publisher_gui_params)
    joint_state_publisher_node = Node(**joint_state_publisher_params)

    rviz_config_file = get_rviz_config_file(context)

    rviz2_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        condition=IfCondition(LaunchConfiguration('use_rviz'))
    )

    return [
        robot_state_publisher_node,
        joint_state_publisher_gui_node,
        joint_state_publisher_node,
        rviz2_node
    ]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_joint_state_publisher_gui', default_value='false',
                              description='Whether to launch joint_state_publisher GUI'),
        DeclareLaunchArgument('use_rviz', default_value='false',
                              description='Whether to launch RViz2'),
        DeclareLaunchArgument('rviz_config', default_value='description',
                              description='Choose which rviz configuration to use'),
        DeclareLaunchArgument('namespace', default_value='',
                              description='Namespace for robot_state_publisher and joint_state_publisher'),
        DeclareLaunchArgument('publish_robot_state', default_value='true',
                              description='Whether to start robot_state_publisher'),
        OpaqueFunction(function=launch_setup)
    ])


if __name__ == '__main__':
    generate_launch_description()