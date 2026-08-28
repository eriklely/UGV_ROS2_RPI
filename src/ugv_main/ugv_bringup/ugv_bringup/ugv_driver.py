#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial  
import json  
from sensor_msgs.msg import JointState
from std_msgs.msg import Float32, Float32MultiArray
import subprocess
import time
import os
from ament_index_python.packages import get_package_share_directory

class UgvDriver(Node):
    def __init__(self, name):
        super().__init__(name)

        # Declare and get serial port parameter (avoids os.walk at import)
        self.declare_parameter('serial_port', '')
        serial_port_param = self.get_parameter('serial_port').get_parameter_value().string_value

        if serial_port_param:
            serial_port = serial_port_param
        else:
            # Fallback: simple platform detection without walking entire filesystem
            if os.path.exists('/dev/ttyTHS1'):
                serial_port = '/dev/ttyTHS1'  # Jetson
            else:
                serial_port = '/dev/ttyAMA0'  # Raspberry Pi / default

        self.get_logger().info(f'Using serial port: {serial_port}')

        # Initialize serial communication with the UGV
        try:
            self.ser = serial.Serial(serial_port, 115200, timeout=1)
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to open serial port {serial_port}: {e}')
            raise

        # Subscribe to velocity commands (cmd_vel topic)
        self.cmd_vel_sub_ = self.create_subscription(Twist, "cmd_vel", self.cmd_vel_callback, 10)

        # Subscribe to joint states (ugv/joint_commands topic)
        self.joint_states_sub = self.create_subscription(JointState, 'joint_commands', self.joint_states_callback, 10)

        # Subscribe to LED control data (led_ctrl topic - relative to namespace)
        self.led_ctrl_sub = self.create_subscription(Float32MultiArray, 'led_ctrl', self.led_ctrl_callback, 10)

        # Subscribe to voltage data (voltage topic)
        self.voltage_sub = self.create_subscription(Float32, 'voltage', self.voltage_callback, 10)

        # Low battery sound state tracking (non-blocking)
        self._low_battery_warning_played = False
        self._low_battery_sound_file = ''
        try:
            pkg_share = get_package_share_directory('ugv_bringup')
            self._low_battery_sound_file = os.path.join(pkg_share, 'low_battery.wav')
        except Exception:
            self._low_battery_sound_file = '/home/ws/ugv_ws/src/ugv_main/ugv_bringup/ugv_bringup/low_battery.wav'

    # Callback for processing velocity commands
    def cmd_vel_callback(self, msg):
        linear_velocity = msg.linear.x
        angular_velocity = msg.angular.z

        # Apply minimum threshold to angular velocity if linear velocity is zero
        epsilon = 1e-6
        if abs(linear_velocity) < epsilon:
            if 0 < angular_velocity < 0.2:
                angular_velocity = 0.2
            elif -0.2 < angular_velocity < 0:
                angular_velocity = -0.2

        # Send the velocity data to the UGV as a JSON string
        # FIX: T must be integer (13), not string '13', for strict ESP32 parser
        data = json.dumps({'T': 13, 'X': linear_velocity, 'Z': angular_velocity}) + "\n"
        self.ser.write(data.encode())

    # Callback for processing joint state updates
    def joint_states_callback(self, msg):
        header = {
            'stamp': {
                'sec': msg.header.stamp.sec,
                'nanosec': msg.header.stamp.nanosec,
            },
            'frame_id': msg.header.frame_id,
        }

        # Extract joint positions and convert to degrees
        name = msg.name
        position = msg.position

        # FIX: Handle missing pan-tilt joints gracefully (don't crash driver)
        try:
            pan_idx = name.index('pt_base_link_to_pt_link1')
            tilt_idx = name.index('pt_link1_to_pt_link2')
        except ValueError:
            self.get_logger().warn('Pan/tilt joint names not found in joint_commands, skipping gimbal command')
            return

        x_rad = position[pan_idx]
        y_rad = position[tilt_idx]

        x_degree = (180 * x_rad) / 3.1415926
        y_degree = (180 * y_rad) / 3.1415926

        # Send the joint data as a JSON string to the UGV
        # Use T=133 (gimbal_ctrl) with SPD/ACC as expected by firmware
        joint_data = json.dumps({
            'T': 133,
            'X': x_degree,
            'Y': y_degree,
            "SPD": 600,
            "ACC": 10,
        }) + "\n"

        self.ser.write(joint_data.encode())

    # Callback for processing LED control commands
    def led_ctrl_callback(self, msg):
        IO4 = msg.data[0]
        IO5 = msg.data[1]

        # Send LED control data as a JSON string to the UGV
        led_ctrl_data = json.dumps({
            'T': 132,
            "IO4": IO4,
            "IO5": IO5,
        }) + "\n"

        self.ser.write(led_ctrl_data.encode())

    # Callback for processing voltage data
    def voltage_callback(self, msg):
        voltage_value = msg.data

        # If voltage drops below a threshold, play a low battery warning sound
        # FIX: Non-blocking - don't sleep in callback, track state instead
        if 0.1 < voltage_value < 9.0:
            if not self._low_battery_warning_played and os.path.exists(self._low_battery_sound_file):
                self._low_battery_warning_played = True
                # Play sound asynchronously (non-blocking)
                try:
                    # Use Popen with DEVNULL to avoid blocking
                    subprocess.Popen(['aplay', '-D', 'plughw:3,0', self._low_battery_sound_file],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                except Exception as e:
                    self.get_logger().warn(f'Failed to play low battery sound: {e}')
        elif voltage_value >= 9.0:
            # Reset warning state when voltage recovers
            self._low_battery_warning_played = False

    def destroy_node(self):
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = UgvDriver("ugv_driver")

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

