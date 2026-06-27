import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    description_pkg = 'amr_description'
    bringup_pkg     = 'amr_bringup'

    xacro_file = os.path.join(get_package_share_directory(description_pkg), 'urdf', 'amr.urdf.xacro')
    robot_description_raw = xacro.process_file(xacro_file).toxml()

    # Custom world: same as empty.sdf + the Sensors system plugin (needed for
    # camera and gpu_lidar — empty.sdf omits it so sensors never activate).
    world_file = os.path.join(get_package_share_directory(bringup_pkg), 'worlds', 'warehouse.sdf')

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_raw, 'use_sim_time': True}]
    )

    # Ignition Gazebo Fortress. '-r' runs immediately.
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r -v 3 {world_file}'}.items(),
    )

    # Bridge sim time from Ignition to ROS so use_sim_time works ([ = gz -> ros).
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[ignition.msgs.Clock'],
        output='screen',
    )

    # Bridge the 2-D lidar scan: Ignition /lidar → ROS /scan
    lidar_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/lidar@sensor_msgs/msg/LaserScan[ignition.msgs.LaserScan'],
        remappings=[('/lidar', '/scan')],
        output='screen',
    )

    # Bridge camera info: Ignition /camera_info → ROS /camera/camera_info
    camera_info_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/camera_info@sensor_msgs/msg/CameraInfo[ignition.msgs.CameraInfo'],
        remappings=[('/camera_info', '/camera/camera_info')],
        output='screen',
    )

    # ros_gz_image handles raw image bridging more reliably than parameter_bridge.
    # Bridges Ignition /camera → ROS /camera/image_raw
    camera_image_bridge = Node(
        package='ros_gz_image',
        executable='image_bridge',
        arguments=['/camera'],
        remappings=[('/camera', '/camera/image_raw')],
        output='screen',
    )

    # Spawn the robot from the robot_description topic into Ignition.
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'warehouse_amr',
                   '-x', '0', '-y', '-10', '-z', '0.1'],
        output='screen',
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    lift_position_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["lift_position_controller", "--controller-manager", "/controller_manager"],
    )

    amr_base_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["amr_base_controller", "--controller-manager", "/controller_manager"],
        parameters=[{'use_sim_time': True}]
    )

    twist_mux = Node(
        package='twist_mux',
        executable='twist_mux',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            os.path.join(get_package_share_directory('amr_bringup'), 'config', 'twist_mux.yaml')
        ],
        remappings=[
            ('/cmd_vel_out', '/amr_base_controller/cmd_vel_unstamped')
        ]
    )

    imu_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/imu@sensor_msgs/msg/Imu[ignition.msgs.IMU'],
        output='screen',
    )

    ekf_node = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_node',
        output='screen',
        parameters=[
            os.path.join(get_package_share_directory('amr_bringup'), 'config', 'ekf.yaml'),
            {'use_sim_time': True},
        ],
    )

    lidar_tf_bridge = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['0', '0', '0', '0', '0', '0',
                'lidar_link', 'warehouse_amr/base_footprint/lidar'],
        output='screen',
    )


    # Controllers start only after the model is spawned, so the gz_ros2_control
    # plugin has created /controller_manager.
    load_controllers = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[
                joint_state_broadcaster_spawner,
                lift_position_controller_spawner,
                amr_base_controller_spawner,
            ]
        )
    )

    return LaunchDescription([
        robot_state_publisher,
        gz_sim,
        clock_bridge,
        lidar_bridge,
        camera_info_bridge,
        camera_image_bridge,
        lidar_tf_bridge,
        spawn_entity,
        twist_mux,
        load_controllers,
        imu_bridge,
        ekf_node,
    ])
