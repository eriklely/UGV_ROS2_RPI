import serial
import json
import queue
import threading
import rclpy
from rclpy.node import Node
import logging
import time
from std_msgs.msg import Header, Float32MultiArray, Float32
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Imu, MagneticField, JointState
import math
import os

def is_jetson():
    result = any("ugv_jetson" in root for root, dirs, files in os.walk("/"))
    return result

if is_jetson():
    serial_port = '/dev/ttyTHS1'
else:
    serial_port = '/dev/ttyAMA0'

# Helper class for reading lines from a serial port
class ReadLine:
    def __init__(self, s):
        self.buf = bytearray()  # Buffer to store incoming data
        self.s = s  # Serial object

    # Read a line of data from the serial input
    def readline(self):
        i = self.buf.find(b"\n")
        if i >= 0:
            r = self.buf[:i+1]
            self.buf = self.buf[i+1:]
            return r
        while True:
            i = max(1, min(512, self.s.in_waiting))  # Read from serial buffer
            data = self.s.read(i)
            i = data.find(b"\n")
            if i >= 0:
                r = self.buf + data[:i+1]
                self.buf[0:] = data[i+1:]
                return r
            else:
                self.buf.extend(data)

    # Clear the buffer
    def clear_buffer(self):
        self.s.reset_input_buffer()

# Base controller class for managing UART communication and processing commands
class BaseController:
    def __init__(self, uart_dev_set, baud_set):
        self.logger = logging.getLogger('BaseController')  # Logger setup
        self.ser = serial.Serial(uart_dev_set, baud_set, timeout=1)  # Open serial connection
        self.rl = ReadLine(self.ser)  # Initialize ReadLine helper
        self.command_queue = queue.Queue()  # Command queue for sending data
        self.command_thread = threading.Thread(target=self.process_commands, daemon=True)  # Start a separate thread for processing commands
        self.command_thread.start()
        self.data_buffer = None  # Buffer for holding received data
        # Base data structure to hold sensor values
        self.base_data = {"T": 1001, "L": 0, "R": 0, "ax": 0, "ay": 0, "az": 0, "gx": 0, "gy": 0, "gz": 0, "mx": 0, "my": 0, "mz": 0, "odl": 0, "odr": 0, "v": 0, "X": 0, "Y": 0}
    
    # Function to read and return feedback data from the serial input
    def feedback_data(self):
        try:
            line = self.rl.readline().decode('utf-8')  # Read line from UART
            self.data_buffer = json.loads(line)  # Parse JSON data
            self.base_data = self.data_buffer  # Store received data
            return self.base_data  # Return base data
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON decode error: {e} with line: {line}")  # Log error
            self.rl.clear_buffer()  # Clear buffer on error
        except Exception as e:
            self.logger.error(f"[base_ctrl.feedback_data] unexpected error: {e}")
            self.rl.clear_buffer()

    # Receive and decode data from the serial connection
    def on_data_received(self):
        # Read line first, then clear buffer to avoid race condition
        line = self.rl.readline().decode('utf-8')
        self.ser.reset_input_buffer()
        data_read = json.loads(line)  # Parse JSON data
        return data_read

    # Add a command to the queue to be sent via UART
    def send_command(self, data):
        self.command_queue.put(data)

    # Thread function to process and send commands from the queue
    def process_commands(self):
        while True:
            data = self.command_queue.get()  # Get command from the queue
            self.ser.write((json.dumps(data) + '\n').encode("utf-8"))  # Send command as JSON over UART

    # Send control data as JSON via UART
    def base_json_ctrl(self, input_json):
        self.send_command(input_json)

# ROS node class for bringing up the UGV system and publishing sensor data
class ugv_bringup(Node):
    def __init__(self):
        super().__init__('ugv_bringup')
        # Declare IMU conversion parameters (defaults for MPU6050)
        self.declare_parameter('accel_scale', 8192.0)  # For +/-4g range
        self.declare_parameter('gyro_scale', 16.4)     # For +/-2000deg/s range
        # Wheel radius parameter for converting odometry to wheel joint angles (default 0.08m = 8cm radius = 160mm diameter)
        self.declare_parameter('wheel_radius', 0.08)
        # Publishers for IMU data, magnetic field data, odometry, voltage, and joint states
        self.imu_data_raw_publisher_ = self.create_publisher(Imu, "imu/data_raw", 100)
        self.imu_mag_publisher_ = self.create_publisher(MagneticField, "imu/mag", 100)
        self.odom_publisher_ = self.create_publisher(Float32MultiArray, "odom/odom_raw", 100)
        self.voltage_publisher_ = self.create_publisher(Float32, "voltage", 50)
        self.joint_states_publisher_ = self.create_publisher(JointState, "joint_states", 50)
        # Initialize the base controller with the UART port and baud rate
        self.base_controller = BaseController(serial_port, 115200)
        # Timer to periodically execute the feedback loop
        # 20Hz (0.05s) - reduced from 1ms (1000Hz) to match serial bandwidth at 115200 baud
        self.feedback_timer = self.create_timer(0.05, self.feedback_loop)

    # Main loop for reading sensor feedback and publishing it to ROS topics
    def feedback_loop(self):
        self.base_controller.feedback_data()
        if self.base_controller.base_data["T"] == 1001:  # Check if the feedback type is correct
            self.publish_imu_data_raw()  # Publish IMU raw data
            self.publish_imu_mag()  # Publish magnetic field data
            self.publish_odom_raw()  # Publish odometry data
            self.publish_voltage()  # Publish voltage data
            self.publish_joint_states()  # Publish joint states (pan/tilt)

    # Publish IMU data to the ROS topic "imu/data_raw"
    def publish_imu_data_raw(self):
        msg = Imu()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()  # Get the current timestamp
        msg.header.frame_id = "base_imu_link"
        imu_raw_data = self.base_controller.base_data

        # Use parameters for IMU conversion (configurable per sensor)
        # Default values for MPU6050: accel_scale=8192 (for +/-4g), gyro_scale=16.4 (for +/-2000deg/s)
        accel_scale = self.get_parameter('accel_scale').get_parameter_value().double_value
        gyro_scale = self.get_parameter('gyro_scale').get_parameter_value().double_value

        # Populate the linear acceleration and angular velocity fields
        msg.linear_acceleration.x = 9.8 * float(imu_raw_data["ax"]) / accel_scale
        msg.linear_acceleration.y = 9.8 * float(imu_raw_data["ay"]) / accel_scale
        msg.linear_acceleration.z = 9.8 * float(imu_raw_data["az"]) / accel_scale
        
        msg.angular_velocity.x = 3.1415926 * float(imu_raw_data["gx"]) / (gyro_scale * 180)
        msg.angular_velocity.y = 3.1415926 * float(imu_raw_data["gy"]) / (gyro_scale * 180)
        msg.angular_velocity.z = 3.1415926 * float(imu_raw_data["gz"]) / (gyro_scale * 180)
              
        self.imu_data_raw_publisher_.publish(msg)  # Publish the IMU data
        
    # Publish magnetic field data to the ROS topic "imu/mag"
    def publish_imu_mag(self):
        msg = MagneticField()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()  # Get the current timestamp
        msg.header.frame_id = "base_imu_link"
        imu_raw_data = self.base_controller.base_data

        # Populate the magnetic field data
        msg.magnetic_field.x = float(imu_raw_data["mx"]) * 0.15
        msg.magnetic_field.y = float(imu_raw_data["my"]) * 0.15
        msg.magnetic_field.z = float(imu_raw_data["mz"]) * 0.15
              
        self.imu_mag_publisher_.publish(msg)  # Publish the magnetic field data

    # Publish odometry data to the ROS topic "odom/odom_raw"
    def publish_odom_raw(self):
        odom_raw_data = self.base_controller.base_data
        array = [odom_raw_data["odl"]/100, odom_raw_data["odr"]/100]
        msg = Float32MultiArray(data=array)
        self.odom_publisher_.publish(msg)  # Publish the odometry data

    # Publish voltage data to the ROS topic "voltage"
    def publish_voltage(self):
        voltage_data = self.base_controller.base_data
        msg = Float32()
        msg.data = float(voltage_data["v"])/100
        self.voltage_publisher_.publish(msg)  # Publish the voltage data

    # Publish joint states (pan/tilt + wheels) to the ROS topic "joint_states"
    def publish_joint_states(self):
        joint_data = self.base_controller.base_data
        msg = JointState()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = "base_link"
        
        # Wheel radius parameter (default 0.08m = 8cm radius = 160mm diameter)
        wheel_radius = self.get_parameter('wheel_radius').get_parameter_value().double_value
        
        # Joint names must match URDF:
        # - 4 wheel joints (continuous): left_up, left_down, right_up, right_down
        # - 2 pan/tilt joints (revolute): pt_base_link_to_pt_link1 (pan), pt_link1_to_pt_link2 (tilt)
        msg.name = [
            "left_up_wheel_link_joint",
            "left_down_wheel_link_joint",
            "right_up_wheel_link_joint",
            "right_down_wheel_link_joint",
            "pt_base_link_to_pt_link1",
            "pt_link1_to_pt_link2"
        ]
        
        # Wheel odometry from hardware (odl, odr in cm, converted to meters by /100)
        # Both wheels on each side share the same position
        odl_m = float(joint_data.get("odl", 0)) / 100.0  # Left wheel distance in meters
        odr_m = float(joint_data.get("odr", 0)) / 100.0  # Right wheel distance in meters
        
        # Convert linear distance to wheel angle (radians)
        # angle = distance / wheel_radius
        left_wheel_angle = odl_m / wheel_radius if wheel_radius > 0 else 0.0
        right_wheel_angle = odr_m / wheel_radius if wheel_radius > 0 else 0.0
        
        # Pan/tilt joints (feedback in degrees, convert to radians)
        pan_deg = float(joint_data.get("X", 0))
        tilt_deg = float(joint_data.get("Y", 0))
        
        msg.position = [
            left_wheel_angle,    # left_up_wheel_link_joint
            left_wheel_angle,    # left_down_wheel_link_joint
            right_wheel_angle,   # right_up_wheel_link_joint
            right_wheel_angle,   # right_down_wheel_link_joint
            pan_deg * math.pi / 180.0,   # pt_base_link_to_pt_link1 (pan)
            tilt_deg * math.pi / 180.0   # pt_link1_to_pt_link2 (tilt)
        ]
        msg.velocity = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        msg.effort = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        self.joint_states_publisher_.publish(msg)
                        
# Main function to initialize the ROS node and start spinning
def main(args=None):
    rclpy.init(args=args)  # Initialize ROS
    node = ugv_bringup()  # Create the UGV bringup node
    rclpy.spin(node)  # Keep the node running
    #node.destroy_node()  # (optional) Shutdown the node
    rclpy.shutdown()  # Shutdown ROS

if __name__ == '__main__':
    main()