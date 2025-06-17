import os
import xacro
import yaml

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction, IncludeLaunchDescription
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def evaluate_nodes(context, *args, **kwargs):

    urdf_path = LaunchConfiguration("urdf_file").perform(context)
    mapping_dict = LaunchConfiguration("urdf_mapping").perform(context)
    mapping_yaml = yaml.safe_load(mapping_dict)

    robot_description = xacro.process_file(urdf_path, mappings=mapping_yaml).toprettyxml(
        indent="  "
    )

    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        parameters=[
            {
                "use_sim_time": LaunchConfiguration("use_sim_time"),
                "robot_description": robot_description,
                "publish_frequency": 100.0,
            }
        ],
        output="screen",
    )

    return [robot_state_publisher_node]


##################################################################
def generate_launch_description():

    desc_dir = get_package_share_directory("go2_description")
    ros_gz_sim_dir = get_package_share_directory("ros_gz_sim")

    launch_args = [
        DeclareLaunchArgument(
            "urdf_file", default_value=os.path.join(desc_dir, "xacro", "robot.urdf.xacro")
        ),
        DeclareLaunchArgument("urdf_mapping", default_value="{}"),
        DeclareLaunchArgument("x", default_value="0.0"),
        DeclareLaunchArgument("y", default_value="0.2"),
        DeclareLaunchArgument("z", default_value="0.5"),
        DeclareLaunchArgument("yaw", default_value="0.4"),
        DeclareLaunchArgument(
            "world", default_value=os.path.join(desc_dir, "worlds", "ionic_reduced.sdf")
        ),  # e.g., ionic_reduced, living_room, ground_plane
        DeclareLaunchArgument("robot_up", default_value="10.0"),
        DeclareLaunchArgument("use_sim_time", default_value="true"),
    ]

    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    z = LaunchConfiguration("z")
    yaw = LaunchConfiguration("yaw")
    world = LaunchConfiguration("world")
    robot_up = LaunchConfiguration("robot_up")

    # Gazebo simulation include
    gz_sim_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([ros_gz_sim_dir, "launch", "gz_sim.launch.py"])
        ),
        launch_arguments={"gz_args": [world, " -r", " -v 4"]}.items(),
    )

    # Spawn go2
    spawn_go2_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([desc_dir, "launch", "spawn_go2.launch.py"])
        ),
        launch_arguments={"x": x, "y": y, "z": z, "yaw": yaw, "robot_up": robot_up}.items(),
    )

    return LaunchDescription(
        launch_args + [gz_sim_launch, OpaqueFunction(function=evaluate_nodes), spawn_go2_launch]
    )
