import ast
from pathlib import Path


LAUNCH_FILE = Path(__file__).resolve().parents[1] / 'launch' / 'bringup_sensors_integrated.launch.py'


def _constant_string(node):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _find_node_calls(tree):
    node_calls = []
    for call in ast.walk(tree):
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == 'Node':
            package = None
            executable = None
            for keyword in call.keywords:
                if keyword.arg == 'package':
                    package = _constant_string(keyword.value)
                if keyword.arg == 'executable':
                    executable = _constant_string(keyword.value)
            node_calls.append((package, executable))
    return node_calls


def _find_declared_arguments(tree):
    argument_names = []
    for call in ast.walk(tree):
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Name) and call.func.id == 'DeclareLaunchArgument':
            if call.args:
                name = _constant_string(call.args[0])
                if name is not None:
                    argument_names.append(name)
    return argument_names


def test_bringup_sensors_integrated_launch_wires_sensor_stack():
    source = LAUNCH_FILE.read_text(encoding='utf-8')
    tree = ast.parse(source)

    node_calls = _find_node_calls(tree)

    assert ('ugv_bringup', 'ugv_bringup') in node_calls
    assert ('ugv_bringup', 'ugv_driver') in node_calls
    assert ('ugv_base_node', 'base_node_ekf') in node_calls
    assert ('nmea_navsat_driver', 'nmea_serial_driver') in node_calls

    assert 'ldlidar.launch.py' in source
    assert 'display.launch.py' in source
    assert "('imu/data_raw', 'imu/data')" in source
    assert "('fix', '/gps/fix')" in source


def test_bringup_sensors_integrated_launch_excludes_heavy_processing():
    source = LAUNCH_FILE.read_text(encoding='utf-8')

    assert 'robot_localization' not in source
    assert 'imu_complementary_filter' not in source
    assert 'imu_filter_madgwick' not in source
    assert 'navsat_transform_node' not in source
    assert 'rviz2' not in source
    assert 'rf2o_laser_odometry' not in source


def test_bringup_sensors_integrated_launch_declares_runtime_gps_args():
    tree = ast.parse(LAUNCH_FILE.read_text(encoding='utf-8'))
    argument_names = _find_declared_arguments(tree)

    assert 'pub_odom_tf' in argument_names
    assert 'gps_port' in argument_names
    assert 'gps_baud' in argument_names
    assert 'gps_frame_id' in argument_names
