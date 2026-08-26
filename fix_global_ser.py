with open('src/ugv_main/ugv_bringup/ugv_bringup/ugv_driver.py', 'r') as f:
    content = f.read()

# Remove the global ser initialization and move it to __init__
# The code before class UgvDriver should not have the ser = serial.Serial(...) line

old = """def is_jetson():
    result = any("ugv_jetson" in root for root, dirs, files in os.walk("/"))
    return result

if is_jetson():
    serial_port = '/dev/ttyTHS1'
else:
    serial_port = '/dev/ttyAMA0'

# Initialize serial communication with the UGV
ser = serial.Serial(serial_port, 115200, timeout=1)

class UgvDriver(Node):"""

new = """def is_jetson():
    result = any("ugv_jetson" in root for root, dirs, files in os.walk("/"))
    return result


class UgvDriver(Node):"""

content = content.replace(old, new)

# Now add the ser initialization in __init__
old_init = """    def __init__(self, name):
        super().__init__(name)

        # Subscribe to velocity commands (cmd_vel topic)"""

new_init = """    def __init__(self, name):
        super().__init__(name)

        # Determine serial port based on platform
        if is_jetson():
            serial_port = '/dev/ttyTHS1'
        else:
            serial_port = '/dev/ttyAMA0'

        # Initialize serial communication with the UGV
        self.ser = serial.Serial(serial_port, 115200, timeout=1)

        # Subscribe to velocity commands (cmd_vel topic)"""

content = content.replace(old_init, new_init)

# Replace all 'ser.' with 'self.ser.'
content = content.replace('ser.write', 'self.ser.write')
content = content.replace('ser.close', 'self.ser.close')
content = content.replace('ser.reset_input_buffer', 'self.ser.reset_input_buffer')

with open('src/ugv_main/ugv_bringup/ugv_bringup/ugv_driver.py', 'w') as f:
    f.write(content)

print("Done")