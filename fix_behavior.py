import re

with open('src/ugv_main/ugv_tools/ugv_tools/behavior_ctrl.py', 'r') as f:
    content = f.read()

# Find and replace the process_commands method
pattern = r'(def process_commands\(self\):.*?)(?=    def odom_callback)'
replacement = '''def process_commands(self):
        # Process the commands in the queue
        # Safe command dispatch table - only allow known methods
        command_map = {
            'stop': self.stop,
            'move': self.move,
            'spin': self.spin,
            'save_point': self.save_map_point,
            'nav_to_point': self.pub_nav_point,
        }
        
        while rclpy.ok():
            command = self.command_queue.get()
            if command is None:
                break
            # Safe command dispatch - no exec/eval
            command_type = command['type']
            data_value = command['data']
            
            if command_type in command_map:
                try:
                    if command_type == 'stop':
                        command_map[command_type]()
                    else:
                        command_map[command_type](data_value)
                except Exception as e:
                    self.get_logger().error(f'Error executing command {command_type}: {e}')
            else:
                self.get_logger().error(f'Unknown command type: {command_type}')
            self.command_queue.task_done()

'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('src/ugv_main/ugv_tools/ugv_tools/behavior_ctrl.py', 'w') as f:
    f.write(content)

print('Replacement done')