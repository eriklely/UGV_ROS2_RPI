import re
content = open(r'C:\Users\Erik.ERIKLELY\Documents\GitHub\UGV_ROS2_RPI\src\ugv_main\ugv_description\urdf\ugv_beast.urdf').read()
joints = re.findall(r'<joint name="([^"]+)"', content)
for j in joints:
    print(j)