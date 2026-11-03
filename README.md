# Mobile Robot Project

ROS 2 and Gazebo Sim mobile robot with camera, IMU, contact sensor, 360-degree LiDAR, and reactive obstacle avoidance.

## Requirements

- ROS 2 Lyrical
- Gazebo Jetty and `ros_gz`
- `colcon`, `xacro`, `rviz2`

## Build and run

From the repository root in a ROS 2 Lyrical environment:

```bash
source /opt/ros/lyrical/setup.bash
rosdep install --from-paths . --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
ros2 launch robot_simulation robot_simulation.launch.py
```

The launch starts Gazebo, the robot, sensor bridges (including `/odom`), and RViz. The robot remains stationary because the behavior node is not started automatically. Start it explicitly in a second terminal when ready:

```bash
source /opt/ros/lyrical/setup.bash
source install/setup.bash
ros2 run robot_behavior obstacle_avoidance
```

To inspect the scan separately, use `ros2 topic echo /scan --once` or select the enabled `LaserScan` display in RViz. The RViz fixed frame is `base_link`; the LiDAR frame is `lidar_link`.

## Person 3: LiDAR and obstacle avoidance

- `robot_description/urdf/lidar.xacro` defines the 360-degree GPU LiDAR: 360 horizontal samples, 10 Hz, 0.12–8.0 m range, mounted on `base_link`.
- `robot_simulation/launch/robot_simulation.launch.py` bridges Gazebo's `/scan` (`gz.msgs.LaserScan`) to ROS 2 `/scan` (`sensor_msgs/msg/LaserScan`).
- `robot_behavior/robot_behavior/obstacle_avoidance.py` subscribes to `/scan` and publishes `geometry_msgs/msg/Twist` on `/cmd_vel`.

### Decision rule

The node checks a broad forward sector (±0.80 rad). At or inside 0.90 m it chooses a turn using the near-front diagonal openings on each side, so a passage ahead-right or ahead-left counts even when it is not directly beside the robot. The side score uses a clearance percentile rather than the single nearest ray. It holds that direction throughout the obstacle to prevent left-right oscillation, and permits one emergency switch only when the chosen side is blocked and the opposite side is clearly open. It keeps turning until the full forward sector is clear beyond 1.20 m, then resumes forward motion at 0.20 m/s with a gentle heading correction. Turn speed is 0.55 rad/s. The test route is aligned with world +X, so the desired `course_heading` defaults to 0.0 rad. Odometry from `/odom` measures the robot's current yaw; avoidance turns are limited to a 90° deviation from the course heading. At that limit, it creeps forward at 0.08 m/s if the front distance remains above 0.90 m; otherwise it stops. For another straight route, set `course_heading` to that route's world-frame angle in radians. Positive angular velocity turns left. Missing odometry, invalid scan metadata, unusable front data, or a scan timeout (0.5 s) produces a zero-velocity command. Positive infinity is treated as no return up to the LiDAR maximum; NaN and negative infinity are discarded.

The run terminal reports each motion-mode change immediately and prints the motion mode, commanded linear/angular speeds, front and side clearances, course error, and odometry state at least every 0.5 seconds.

These values are ROS parameters on `obstacle_avoidance` and can be overridden in the launch file or with ROS parameter tools.

## Manual behavior check

The obstacle world contains a first test box followed by alternating gate openings, side rails, and an end wall. Start the simulation first and confirm the robot is stationary, then run the behavior node in a second terminal. In RViz check the `/scan` display; in another terminal run `ros2 topic echo /cmd_vel`. The robot should turn away before reaching each barrier, keep its chosen turn direction until there is a wider forward gap, and move forward again. Stop the behavior node with Ctrl+C; the simulation can remain open for inspection. Record the Gazebo/RViz views and topic output for the project demonstration/report.
