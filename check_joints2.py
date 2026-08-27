with open(r'C:\Users\Erik.ERIKLELY\Documents\GitHub\UGV_ROS2_RPI\src\ugv_main\ugv_description\urdf\ugv_beast.urdf') as f:
    content = f.read()

import re
joints = re.findall(r'<joint name="([^"]+)" type="([^"]+)"', content)
for name, jtype in joints:
    print(f'{name}: {jtype}')