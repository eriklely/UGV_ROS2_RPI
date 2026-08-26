with open('src/ugv_main/ugv_vision/ugv_vision/gesture_ctrl.py', 'r') as f:
    content = f.read()

old = """        # Loop through the landmarks
        for id,lm in enumerate(hand_landmarks.landmark):
         
          # Get the height, width, and channels of the image
          h,w,c= 480,640,3
          # Get the x and y coordinates of the landmark
          cx,cy=int(lm.x * w) , int(lm.y * h)"""

new = """        # Loop through the landmarks
        for id,lm in enumerate(hand_landmarks.landmark):
         
          # Get the height, width, and channels of the image
          h, w, c = frame.shape
          # Get the x and y coordinates of the landmark
          cx,cy=int(lm.x * w) , int(lm.y * h)"""

content = content.replace(old, new)

with open('src/ugv_main/ugv_vision/ugv_vision/gesture_ctrl.py', 'w') as f:
    f.write(content)

print('Done')