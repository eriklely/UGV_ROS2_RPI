with open('src/ugv_main/ugv_vision/ugv_vision/color_track.py', 'r') as f:
    content = f.read()

old = """        # Convert the OpenCV image to an image message
        result_img_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")                                                                                     
        # Publish the image message
        self.color_track_publisher.publish(result_img_msg)
        # Show the image
        cv2.imshow('Tracked Image', frame)
        # Wait for a key press
        cv2.waitKey(1)

def main(args=None):"""

new = """        # Convert the OpenCV image to an image message
        result_img_msg = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
        # Publish the image message
        self.color_track_publisher.publish(result_img_msg)

def main(args=None):"""

content = content.replace(old, new)

with open('src/ugv_main/ugv_vision/ugv_vision/color_track.py', 'w') as f:
    f.write(content)

print('Done')