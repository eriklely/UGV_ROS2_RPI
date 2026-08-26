with open('src/ugv_main/ugv_bringup/ugv_bringup/ugv_bringup.py', 'r') as f:
    content = f.read()

old = """        # Populate the linear acceleration and angular velocity fields
        msg.linear_acceleration.x = 9.8 * float(imu_raw_data[\"ax\"]) / 8192
        msg.linear_acceleration.y = 9.8 * float(imu_raw_data[\"ay\"]) / 8192
        msg.linear_acceleration.z = 9.8 * float(imu_raw_data[\"az\"]) / 8192
        
        msg.angular_velocity.x = 3.1415926 * float(imu_raw_data[\"gx\"]) / (16.4 * 180)
        msg.angular_velocity.y = 3.1415926 * float(imu_raw_data[\"gy\"]) / (16.4 * 180)
        msg.angular_velocity.z = 3.1415926 * float(imu_raw_data[\"gz\"]) / (16.4 * 180)"""

new = """        # Use parameters for IMU conversion (configurable per sensor)
        # Default values for MPU6050: accel_scale=8192 (for +/-4g), gyro_scale=16.4 (for +/-2000deg/s)
        accel_scale = self.get_parameter('accel_scale').get_parameter_value().double_value
        gyro_scale = self.get_parameter('gyro_scale').get_parameter_value().double_value

        # Populate the linear acceleration and angular velocity fields
        msg.linear_acceleration.x = 9.8 * float(imu_raw_data[\"ax\"]) / accel_scale
        msg.linear_acceleration.y = 9.8 * float(imu_raw_data[\"ay\"]) / accel_scale
        msg.linear_acceleration.z = 9.8 * float(imu_raw_data[\"az\"]) / accel_scale
        
        msg.angular_velocity.x = 3.1415926 * float(imu_raw_data[\"gx\"]) / (gyro_scale * 180)
        msg.angular_velocity.y = 3.1415926 * float(imu_raw_data[\"gy\"]) / (gyro_scale * 180)
        msg.angular_velocity.z = 3.1415926 * float(imu_raw_data[\"gz\"]) / (gyro_scale * 180)"""

content = content.replace(old, new)

with open('src/ugv_main/ugv_bringup/ugv_bringup/ugv_bringup.py', 'w') as f:
    f.write(content)

print('Done')