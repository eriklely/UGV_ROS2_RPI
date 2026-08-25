# UGV ROVER / BEAST — GPS/EKF Deployment Checklist

Use this checklist every time you bring up the GPS/EKF localization stack in
the field.  Work through the sections in order; each section depends on the
previous one being healthy.

---

## 1. Pre-Flight Hardware Checks

- [ ] GPS antenna has clear sky view (>120° cone above horizon, no overhead obstructions)
- [ ] GPS module is powered and its LED status matches "fix acquired" for your hardware
- [ ] IMU is mounted flat, connectors secure, no loose cables near motor drivers
- [ ] Lidar is mounted level and spinning (if `use_lidar_odom:=true`)
- [ ] Battery voltage is ≥ threshold (check `/battery_state` or physical gauge)

---

## 2. Stack Startup

```bash
# Terminal 1 — Main localization stack (GPS enabled)
ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=true

# Terminal 1 — With lidar odometry fusion (optional fallback)
ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=true use_lidar_odom:=true

# Terminal 1 — Override magnetic declination for your region (Netherlands example)
ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=true mag_declination:=0.0349
```

- [ ] Terminal shows `GPS mode ENABLED` log line
- [ ] No `TF_OLD_DATA` or `LookupException` warnings in the first 10 seconds

---

## 3. GPS Fix Quality Check

```bash
ros2 topic echo /gps/fix --once
```

- [ ] `status.status` ≥ 0  (0 = standard fix, 1 = SBAS, 2 = GBAS/RTK)
- [ ] `position_covariance[0]` < 4.0 m²  (σ < 2 m, values > 9 indicate poor fix)
- [ ] `position_covariance_type` ≥ 1  (APPROXIMATED or DIAGONAL_KNOWN)
- [ ] Latitude / longitude values are plausible for your location

> **Tip**: If covariance > 9 m² wait for more satellites or move to a more
> open area before proceeding.

---

## 4. Frame Alignment Verification

```bash
# Terminal 2 — TF tree snapshot (generates /tmp/frames.pdf)
ros2 launch ugv_bringup diagnostics.launch.py

# Open the PDF
xdg-open /tmp/frames.pdf       # Linux
open /tmp/frames.pdf           # macOS
```

- [ ] `map → odom → base_footprint` chain visible in frames.pdf
- [ ] Only **one** publisher for `odom → base_footprint` (the local EKF)
- [ ] `map → odom` published by `ekf_filter_node_map` only when GPS is active
- [ ] No dangling or disconnected frames

```bash
# Verify transforms are being published and are fresh (< 0.1 s old)
ros2 run tf2_ros tf2_echo odom base_footprint
ros2 run tf2_ros tf2_echo map odom
```

- [ ] `tf2_echo odom base_footprint` outputs continuously without gaps
- [ ] `tf2_echo map odom` outputs continuously when GPS is active

---

## 5. Odometry Continuity Test

```bash
# Drive the robot in a straight line for 2–3 m at normal walking speed,
# then check that /odom increments smoothly
ros2 topic echo /odom
```

- [ ] `pose.pose.position.x` increases monotonically during forward motion
- [ ] No sudden jumps > 0.1 m between consecutive messages
- [ ] `pose.covariance[0]` (x variance) stays < 0.5 m² during normal driving
- [ ] Angular rate (twist.twist.angular.z) is near 0 during straight driving

---

## 6. Heading Initialization (World-Lock) Validation

```bash
# After driving 2–3 m straight, echo the GPS-derived odometry
ros2 topic echo /odometry/gps --once
```

- [ ] `pose.pose.position.x` or `y` has changed in the direction of travel
- [ ] No sign reversal compared to `/odom` — both should show the same direction
- [ ] `header.stamp` is recent (< 1 s old)

```bash
# Confirm global odometry is publishing
ros2 topic echo /odometry/global --once
```

- [ ] Topic is active and stamp is fresh
- [ ] Position matches `/odometry/gps` within a few metres

> **If heading is 90° or 180° off**: Check `yaw_offset` in
> `navsat_transform_params.yaml`.  A 90° error usually means the IMU X-axis
> does not align with the robot's forward direction.

---

## 7. (Optional) Set a Fixed Datum

Use this step when you need repeatable map-frame coordinates across power cycles.

```bash
# List built-in reference locations
ros2 run ugv_bringup set_datum --list

# Set datum by name (add your location to ugv_bringup/set_datum.py)
ros2 run ugv_bringup set_datum --location wavecrest_lab

# Set datum by coordinates
ros2 run ugv_bringup set_datum --lat 52.3676 --lon 4.9041 --alt 0.0
```

- [ ] Script prints `Datum set successfully`
- [ ] `/odometry/global` position is now relative to the supplied coordinates
- [ ] Verify with `ros2 topic echo /odometry/global --once`

---

## 8. EKF Health Check

```bash
ros2 topic echo /diagnostics | grep -A 5 "ekf"
```

- [ ] No `WARN` or `ERROR` level entries from `ekf_filter_node` or `ekf_filter_node_map`
- [ ] Innovation scores (if printed) are not persistently > 3.0 σ

---

## 9. Nav2 Readiness (if using GPS waypoint following)

- [ ] Steps 1–8 all passed
- [ ] Costmaps are in rolling-window mode (no static-layer errors)
- [ ] `ros2 topic echo /map` is silent (outdoor GPS nav does not require a static map)
- [ ] Navigation stack launched **after** world-lock confirmed in step 6

---

## Common Failure Modes

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `map → odom` never appears | GPS fix never acquired / `use_gps:=false` | Check antenna, set `use_gps:=true` |
| Pose jumps 10–15 m | GPS outlier accepted | Lower `odom1_pose_rejection_threshold` in `ekf_gps.yaml` |
| Heading 90° off at world-lock | Wrong `yaw_offset` | Set `yaw_offset` in `navsat_transform_params.yaml` |
| Heading 180° off | GPS velocity sign inverted | Drive faster (> 0.5 m/s) during init or check GPS module orientation |
| `/odometry/gps` not publishing | `navsat_transform_node` not converged | Drive straight 2–3 m; check IMU is publishing |
| Odometry drifts rapidly indoors | No GPS correction, wheel slip | Enable `use_lidar_odom:=true` for lidar-odom fallback |
| `TF_OLD_DATA` warnings | System time jump or slow node | Set `reset_on_time_jump: true` in EKF config |

---

*Generated by UGV_ROS2_RPI project — update this file when deployment environment changes.*
