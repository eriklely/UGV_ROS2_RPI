with open('src/ugv_main/ugv_vision/ugv_vision/gesture_ctrl.py', 'r') as f:
    content = f.read()

old = """        result_img_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")                                                                                     
        # Publish the image
        self.gesture_ctrl_publisher.publish(result_img_msg)
        # Show the image
        cv2.imshow('Tracked Image', frame)
        # Wait for a key press
        cv2.waitKey(1)

def main(args=None):"""

new = """        result_img_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        # Publish the image
        self.gesture_ctrl_publisher.publish(result_img_msg)

def main(args=None):"""

content = content.replace(old, new)

with open('src/ugv_main/ugv_vision/ugv_vision/gesture_ctrl.py', 'w') as f:
    f.write(content)

print('Done')