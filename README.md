# Mobile Robot Project

A differential-drive mobile robot simulation developed using **ROS 2 Lyrical, Gazebo Jetty, and RViz 2**.

The project includes a custom URDF/Xacro robot model, four integrated sensors (Camera, IMU, Contact Sensor, and LiDAR), and a LiDAR-based reactive obstacle avoidance algorithm.

Gazebo is used for robot simulation, while ROS 2 and RViz 2 are used for sensor communication and visualization.

## 1. Requirements

The project was developed and tested on Ubuntu 26.04 using:

- ROS 2 Lyrical
- Gazebo Jetty
- `ros_gz_sim`, `ros_gz_bridge`, `ros_gz_interfaces`
- `robot_state_publisher`, `xacro`, `rviz2`
- Python 3
- `colcon`, `rosdep`

ROS 2, Gazebo, and the ROS–Gazebo integration packages must be installed before building the project.

## 2. Project Structure

The repository contains three ROS 2 packages and a test results directory.

```text
mobile_robot_project/
├── robot_description/
│   ├── urdf/
│   │   ├── robot.urdf.xacro
│   │   ├── camera.xacro
│   │   ├── imu.xacro
│   │   ├── contact_sensor.xacro
│   │   └── lidar.xacro
│   ├── CMakeLists.txt
│   └── package.xml
│
├── robot_simulation/
│   ├── launch/
│   │   └── robot_simulation.launch.py
│   ├── config/
│   │   ├── contact_bridge.yaml
│   │   └── mobile_robot.rviz
│   ├── worlds/
│   │   ├── imu_world.sdf
│   │   ├── test_world.world
│   │   └── obstacle_world.sdf
│   ├── CMakeLists.txt
│   └── package.xml
│
├── robot_behavior/
│   ├── robot_behavior/
│   │   ├── __init__.py
│   │   └── obstacle_avoidance.py
│   ├── resource/
│   ├── setup.py
│   ├── setup.cfg
│   └── package.xml
│
├── test_results/
│   ├── camera/
│   ├── contact/
│   ├── lidar/
│   ├── obstacle_world/
│   └── imu_and_motion_tests.md
│
└── README.md
```

- **robot_description:** Robot model and sensor descriptions.
- **robot_simulation:** Gazebo worlds, launch files, RViz configuration, and sensor bridges.
- **robot_behavior:** LiDAR-based obstacle avoidance algorithm.
- **test_results:** Sensor measurements, screenshots, and test reports.

## 3. Installation and Build

### Clone the Repository

```bash
git clone https://github.com/Esma-HHO/mobile_robot_project.git
cd mobile_robot_project
```

### Install Dependencies and Build

Run the following commands from the repository root:

```bash
source /opt/ros/lyrical/setup.bash

rosdep install --from-paths . --ignore-src -r -y

colcon build --symlink-install

source install/setup.bash
```

**Note:** ROS 2 and Gazebo must already be installed, and `rosdep` must be initialized before running these commands.

## 4. Running the Project

### Start the Simulation

From the repository root, run:

```bash
ros2 launch robot_simulation robot_simulation.launch.py
```

This command launches Gazebo, spawns the robot, starts the sensor bridges, and opens RViz 2.

The default simulation environment is `obstacle_world.sdf`.

### Start Obstacle Avoidance

Keep the simulation running and open a second terminal.

Navigate to the repository root and execute:

```bash
source /opt/ros/lyrical/setup.bash
source install/setup.bash

ros2 run robot_behavior obstacle_avoidance
```

The robot uses LiDAR and odometry data to detect obstacles, select a turning direction, and continue moving when the path is clear.


## 5. Sensors and ROS 2 Topics

The robot includes four sensor types integrated into the Gazebo simulation.

| Sensor | ROS 2 Topic | Description |
|---|---|---|
| Camera | `/camera/image_raw` | Front-mounted RGB camera, 640 × 480, 30 Hz |
| IMU | `/imu/data` | Orientation, angular velocity, and acceleration |
| Contact Sensor | `/contact` | Front bumper collision detection |
| LiDAR | `/scan` | 360° obstacle detection |

Sensor data is transferred from Gazebo to ROS 2 using the configured bridges.

Camera images and LiDAR measurements can be visualized in RViz 2.

Robot movement commands are published through `/cmd_vel`, and odometry data is available through `/odom`.

## 6. Simulation and Test Results

The repository includes Gazebo worlds used for sensor verification and obstacle avoidance testing.

- **imu_world.sdf:** Initial robot and IMU simulation.
- **test_world.world:** Camera and contact sensor testing with a static obstacle.
- **obstacle_world.sdf:** Multi-obstacle environment used for navigation testing.

Sensor and simulation tests were performed using Gazebo, ROS 2 topics, and RViz 2.

Recorded measurements, screenshots, and test reports are available in the [`test_results`](test_results/) directory.

## 10. Team Contributions

### Person 1 — Esma Hacıhasanoğlu ([@Esma-HHO](https://github.com/Esma-HHO))
**Robot Design, Differential Drive, and IMU**

- Designed the robot body and differential-drive system.
- Integrated the IMU sensor.
- Configured robot movement and odometry.
- Prepared the initial imu world.
- Recorded movement and IMU test results.

### Person 2 — Huriser Ergün ([@Hurisser](https://github.com/Hurisser))
**Camera, Contact Sensor, and Simulation Integration**

- Integrated and tested the camera and front contact sensor.
- Configured Gazebo–ROS 2 sensor bridges.
- Prepared test world and an extended obstacle environment.
- Updated simulation launch and RViz configurations.
- Recorded camera measurements and test reports.

### Person 3 — Emine Ersöz ([@erszemine](https://github.com/erszemine))
**LiDAR and Obstacle Avoidance**

- Integrated the 360-degree LiDAR sensor.
- Configured LiDAR publishing and RViz visualization.
- Developed the reactive obstacle avoidance algorithm.
- Further developed the obstacle world for navigation testing.
- Recorded LiDAR measurements and obstacle avoidance test results.
