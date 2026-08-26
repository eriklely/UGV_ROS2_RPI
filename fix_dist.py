with open('src/ugv_main/ugv_tools/ugv_tools/behavior_ctrl.py', 'r') as f:
    lines = f.readlines()

# Fix drive_on_heading function (starts around line 129, first "Store the start distance" is around line 140)
# We need to modify lines 139-156 (0-indexed: 138-155)

# Find the first "Store the start distance" in drive_on_heading
for i in range(130, 160):
    if 'Store the start distance' in lines[i]:
        idx1 = i
        break

print(f"First 'Store the start distance' at line {idx1+1}")

# Insert the fix after the comment line
# The structure is:
# idx1: "# Store the start distance\n"
# idx1+1: "        start_distance = self.distance\n"
# idx1+2: "        print('start distance:', start_distance)\n"
# idx1+3: "           \n"
# idx1+4: "        # Calculate the delta distance\n"
# ...

# We need to change idx1+1 and idx1+2, and modify the loop body
lines[idx1] = '        # Store the start distance\n'
lines.insert(idx1 + 1, '        # Copy position values to avoid reference issues (self.distance may be updated by odom_callback)\n')
lines[idx1 + 2] = '        start_distance = self.distance\n'
lines[idx1 + 3] = "        start_x = start_distance.x\n"
lines.insert(idx1 + 4, "        start_y = start_distance.y\n")
lines[idx1 + 5] = "        print('start distance:', start_x, start_y)\n"

# Now we need to modify the loop body - find the diff_x and diff_y lines
for i in range(idx1 + 6, idx1 + 20):
    if 'diff_x = self.distance.x - start_distance.x' in lines[i]:
        lines[i] = '            diff_x = self.distance.x - start_x\n'
        print(f"Fixed diff_x at line {i+1}")
    if 'diff_y = self.distance.y - start_distance.y' in lines[i]:
        lines[i] = '            diff_y = self.distance.y - start_y\n'
        print(f"Fixed diff_y at line {i+1}")

# Find the second "Store the start distance" in back_up function
for i in range(160, 200):
    if 'Store the start distance' in lines[i]:
        idx2 = i
        break

print(f"Second 'Store the start distance' at line {idx2+1}")

# Apply same fix to back_up
lines[idx2] = '        # Store the start distance\n'
lines.insert(idx2 + 1, '        # Copy position values to avoid reference issues (self.distance may be updated by odom_callback)\n')
lines[idx2 + 2] = '        start_distance = self.distance\n'
lines[idx2 + 3] = "        start_x = start_distance.x\n"
lines.insert(idx2 + 4, "        start_y = start_distance.y\n")
lines[idx2 + 5] = "        print('start distance:', start_x, start_y)\n"

# Modify the loop body in back_up
for i in range(idx2 + 6, idx2 + 20):
    if 'diff_x = self.distance.x - start_distance.x' in lines[i]:
        lines[i] = '            diff_x = self.distance.x - start_x\n'
        print(f"Fixed back_up diff_x at line {i+1}")
    if 'diff_y = self.distance.y - start_distance.y' in lines[i]:
        lines[i] = '            diff_y = self.distance.y - start_y\n'
        print(f"Fixed back_up diff_y at line {i+1}")

with open('src/ugv_main/ugv_tools/ugv_tools/behavior_ctrl.py', 'w') as f:
    f.writelines(lines)

print("Done")