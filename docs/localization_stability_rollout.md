# Localization Stability Rollout

## Summary

Parameter-only changes to stabilize the robot localization stack in `UGV_ROS2_RPI`.  
No launcher structure was changed. All existing functionality (local-only mode and GPS-enabled mode) is preserved.  
These exact same file edits must be replicated to `UGV_ROS2_LAPTOP` and `UGV_ROS2_DESKTOP`.

---

## Files Changed

| File | Purpose |
|---|---|
| `src/ugv_main/ugv_bringup/param/ekf.yaml` | Local EKF (odom frame) — always active |
| `src/ugv_main/ugv_bringup/param/ekf_gps.yaml` | Global EKF (map frame) — active when `use_gps:=true` |
| `src/ugv_main/ugv_bringup/param/imu_filter_param.yaml` | Madgwick IMU filter |

---

## Parameter Changes

### `ekf.yaml` — Local EKF

| Parameter | Old value | New value | Rationale |
|---|---|---|---|
| `sensor_timeout` | `0.1` | `0.5` | 0.1 s at 30 Hz means only 3 missed messages before a predict-only cycle. 0.5 s gives the filter more tolerance for brief sensor gaps without oscillating. |
| `transform_timeout` | `0.0` | `0.1` | Zero means no retry on TF lookup failure, causing intermittent TF errors under load. 0.1 s gives the listener time to receive the transform. |
| `odom0_pose_rejection_threshold` | `20.0` | `5.0` | 20.0 (Mahalanobis) is far too permissive; outlier wheel odom poses pass straight through. 5.0 keeps the gate effective without over-rejecting. |
| `odom0_twist_rejection_threshold` | `1.542` | `3.0` | 1.542 is too tight and frequently rejects valid odom twist measurements, causing sudden heading/velocity jumps. 3.0 reduces spurious rejections. |
| `imu0_relative` | `true` | `false` | `imu0_relative: true` resets the IMU yaw reference to zero at startup and integrates incrementally. The same yaw is also fused absolutely via `odom0_config`. This creates a fight between relative IMU yaw and absolute odom yaw → the most common cause of heading wobble. Setting `false` lets the EKF treat IMU yaw as absolute (consistent with ENU world frame). |
| `imu0_pose_rejection_threshold` | `20.0` | `5.0` | Same reasoning as `odom0_pose_rejection_threshold`. |
| `imu0_twist_rejection_threshold` | `1.542` | `3.0` | Same reasoning as `odom0_twist_rejection_threshold`. |
| `initial_estimate_covariance` (all diagonals) | `1e-9` | `0.1` | Near-zero initial covariance tells the EKF it is already perfectly certain about the initial state. This makes it extremely slow to incorporate the first real measurements, producing large delayed corrections (visible as a lurch/jump after a few seconds). `0.1` is a realistic starting uncertainty that lets the filter converge smoothly from the first cycle. |

### `ekf_gps.yaml` — Global EKF (GPS mode)

| Parameter | Old value | New value | Rationale |
|---|---|---|---|
| `sensor_timeout` | `0.1` | `0.5` | Same as local EKF. |
| `transform_timeout` | `0.0` | `0.1` | Same as local EKF. |
| `odom0_pose_rejection_threshold` | `20.0` | `5.0` | Same as local EKF. |
| `odom0_twist_rejection_threshold` | `1.542` | `3.0` | Same as local EKF. |
| `odom1_pose_rejection_threshold` | `2.0` | `5.0` | GPS-derived odometry naturally has multi-metre noise. A threshold of 2.0 (Mahalanobis) rejects almost every GPS correction, making the global EKF useless. 5.0 allows realistic GPS corrections to pass while still rejecting gross outliers. |
| `odom1_twist_rejection_threshold` | `1.0` | `3.0` | Same reasoning — too tight for GPS-velocity data quality. |
| `imu0_relative` | `true` | `false` | Same reasoning as local EKF. Consistent heading reference across both EKF instances. |
| `imu0_pose_rejection_threshold` | `20.0` | `5.0` | Same as local EKF. |
| `imu0_twist_rejection_threshold` | `1.542` | `3.0` | Same as local EKF. |
| `initial_estimate_covariance` (all diagonals) | `1e-9` | `0.1` | Same as local EKF. |

### `imu_filter_param.yaml` — Madgwick Filter

| Parameter | Old value | New value | Rationale |
|---|---|---|---|
| `fixed_frame` | `"base_link"` | `"base_footprint"` | Both EKF instances use `base_link_frame: base_footprint`. The IMU filter's `fixed_frame` must match so that the produced `/imu/data` orientation is expressed relative to the correct body frame. A mismatch causes subtle heading offsets that appear as constant drift. |

---

## TF Ownership

No changes were made to TF publishers. The ownership contract remains:

- `odom → base_footprint`: published by the local EKF (`ekf_filter_node`). The `base_node_ekf` node has `pub_odom_tf: false` (controlled via the `pub_odom_tf` launch arg, which defaults to `false`).
- `map → odom`: published by the global EKF (`ekf_filter_node_map`) only when `use_gps:=true`.

---

## Validation Checklist

### Test A — Local-only mode (`use_gps:=false`)

1. `ros2 launch ugv_bringup bringup_imu_ekf.launch.py`
2. Let the robot sit still for 10 s — `/odom` position must not drift more than ±1 cm.
3. Drive forward 1 m — `/odom` X should increase by ~1 m, yaw must not oscillate during straight motion.
4. Rotate 90° — `/odom` yaw should change by ~1.57 rad without bouncing back.
5. `ros2 topic hz /odom` must show ~30 Hz.
6. `ros2 run tf2_tools view_frames` — confirm exactly one `odom → base_footprint` edge.

### Test B — GPS-enabled mode (`use_gps:=true`)

1. `ros2 launch ugv_bringup bringup_imu_ekf.launch.py use_gps:=true`
2. Wait for GPS fix (`/gps/fix` not empty).
3. Drive straight 3 m to initialise navsat heading (world-lock).
4. Check `/odometry/global` is publishing at ~30 Hz with no jumps > 0.5 m.
5. `ros2 run tf2_tools view_frames` — confirm `map → odom → base_footprint` chain, no duplicate edges.
6. Disable GPS fix (or block signal) — robot must continue navigating on local odom without crash.

---

## Copy Checklist for `UGV_ROS2_LAPTOP` and `UGV_ROS2_DESKTOP`

Apply the identical changes to the same files in each sister repo.  
Hardware-specific settings (serial ports, topic names, device IDs) are **not** in these files and do not need to change.

- [ ] Copy `src/ugv_main/ugv_bringup/param/ekf.yaml` from this PR or apply the table above manually.
- [ ] Copy `src/ugv_main/ugv_bringup/param/ekf_gps.yaml` from this PR or apply the table above manually.
- [ ] Copy `src/ugv_main/ugv_bringup/param/imu_filter_param.yaml` from this PR or apply the table above manually.
- [ ] Run validation checklist Test A on each machine.
- [ ] Run validation checklist Test B on each machine (if GPS hardware is present).
