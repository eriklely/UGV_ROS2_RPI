with open('src/ugv_main/ugv_vision/ugv_vision/apriltag.py', 'r') as f:
    content = f.read()

old = """        # Convert the OpenCV image back to a ROS Image message
        result_img_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")                                                                                     
        # Publish the result image message
        self.apriltag_ctrl_publisher.publish(result_img_msg)
        # Show the result image
        cv2.imshow('ctrled Image', frame)
        # Wait for 1 millisecond
        cv2.waitKey(1)

def main"""

new = """        # Convert the OpenCV image back to a ROS Image message
        result_img_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        # Publish the result image message
        self.apriltag_ctrl_publisher.publish(result_img_msg)

def main"""

content = content.replace(old, new)

with open('src/ugv_main/ugv_vision/ugv_vision/apriltag.py', 'w') as f:
    f.write(content)

print('Done')