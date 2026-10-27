
import os

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    description_dir = get_package_share_directory('robot_description')
    simulation_dir = get_package_share_directory('ros_gz_sim')
    robot_simulation_dir = get_package_share_directory('robot_simulation')
    rviz_config_file = os.path.join(
    robot_simulation_dir,
    'config',
    'mobile_robot.rviz'
    )

    xacro_file = os.path.join(
        description_dir, 'urdf', 'robot.urdf.xacro'
    )

    world_file = os.path.join(
        robot_simulation_dir,
        'worlds',
        'test_world.world'
    )

    robot_description = {
        'robot_description': Command(['xacro ', xacro_file])
    }

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                simulation_dir, 'launch', 'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': f'-r {world_file}'
        }.items()
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[robot_description]
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'
        ],
        output='screen'
    )

    cmd_vel_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist'
        ],
        output='screen'
    )

    imu_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/imu/data@sensor_msgs/msg/Imu[gz.msgs.IMU'
        ],
        output='screen'
    )

    camera_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            '/camera/image_raw@sensor_msgs/msg/Image[gz.msgs.Image',
            '/camera/camera_info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo'
        ],
        output='screen'
    )

    contact_bridge_config = os.path.join(
    robot_simulation_dir,
    'config',
    'contact_bridge.yaml'
    )

    contact_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='contact_bridge',
        parameters=[{
            'config_file': contact_bridge_config
        }],
        output='screen'
    )

    spawn_robot = TimerAction(
        period=3.0,
        actions=[
            Node(
                package='ros_gz_sim',
                executable='create',
                arguments=[
                    '-world', 'empty',
                    '-topic', 'robot_description',
                    '-name', 'mobile_robot',
                    '-z', '0.15'
                ],
                output='screen'
            )
        ]
    )

    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': True}]
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        clock_bridge,
        cmd_vel_bridge,
        imu_bridge,
        camera_bridge,
        contact_bridge,
        spawn_robot,
        rviz_node
    ])
