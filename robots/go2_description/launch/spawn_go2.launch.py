from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node, SetParameter
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable, OpaqueFunction
from launch.actions import RegisterEventHandler
from launch.actions import IncludeLaunchDescription
from launch.actions import ExecuteProcess, TimerAction
from launch.event_handlers import OnProcessExit, OnExecutionComplete
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, Command, PathJoinSubstitution, FindExecutable
from launch.substitutions import PythonExpression
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.substitutions import FindPackageShare

from os import environ
import os
import xacro
import yaml

def evaluate_pose(context, *args, **kwargs):

  # Robot gonna fall at the beginning. Here we pick it up
  x = LaunchConfiguration("x").perform(context)
  y = LaunchConfiguration("y").perform(context)
  z = LaunchConfiguration("z").perform(context)

  position="position: {x: " + x + ", y: " + y + ", z: " + z + "}"
  request_string = 'name: "go2", ' + position
  stand_up = ExecuteProcess(cmd=['gz', 'service', '-s', '/world/demo/set_pose',
             '--reqtype', 'gz.msgs.Pose', '--reptype', 'gz.msgs.Boolean', '--timeout', '1000',
             '--req', request_string],
             name="stand_up",
             output="both")

  return [stand_up]

##################################################################
def generate_launch_description():

  launch_args = [
    DeclareLaunchArgument("robot_base_link", default_value="base"),
    DeclareLaunchArgument(
        'x',
        default_value='0.0',
        description='X at which to spawn Spot. 0.84 for ground plane, 0 for marsyard is good'),
    DeclareLaunchArgument(
        'y',
        default_value='0.0',
        description='y at which to spawn Spot.'),
    DeclareLaunchArgument(
        'z',
        default_value='0.84',
        description='Height at which to spawn Spot.'),
    DeclareLaunchArgument(
        'roll',
        default_value='0.0',
        description='Roll at which to spawn Spot.'),
    DeclareLaunchArgument(
        'yaw',
        default_value='-0.5',
        description='Yaw at which to spawn Spot.'),
    DeclareLaunchArgument(
        'robot_up',
        default_value='7.0',
        description='Time that we wait till we send a set_pose command to set robot standing up.'),
    DeclareLaunchArgument(
        'use_simulator',
        default_value='True',
        description='whether to use Gazebo Simulation.'),
    DeclareLaunchArgument(
        'use_sim_time',
        default_value='True',
        description='If true, use simulated clock'),
    DeclareLaunchArgument(
        'tf_prefix',
        default_value='',
        description='...'),
    DeclareLaunchArgument(
        'localization_params',
        default_value=os.path.join(
            get_package_share_directory('champ_bringup'), 'config', 'robot_localization_params.yaml'),
        description='Path to the vox_nav parameters file.'),
    DeclareLaunchArgument(
        'start_quadruped_controller', default_value='True')
  ]

  use_simulator = LaunchConfiguration('use_simulator')
  use_sim_time = LaunchConfiguration('use_sim_time', default=True)
  tf_prefix = LaunchConfiguration('tf_prefix')

  # Bridge
  bridge_config_file = os.path.join(get_package_share_directory('champ_bringup'), 'config', "go2_bridge.yaml")

  bridge = Node(
      package='ros_gz_bridge',
      executable='parameter_bridge',
      parameters=[{'config_file': bridge_config_file}],
      #arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
      output='screen'
  )

  # Spawn the robot in Ignition Gazebo
  spawn_entity_to_gazebo_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'go2',
                   '-topic', '/robot_description',
                    "-x", LaunchConfiguration("x"),
                    "-y", LaunchConfiguration("y"),
                   "-z", LaunchConfiguration("z"),
                   "-R", LaunchConfiguration("roll"),
                   "-Y", LaunchConfiguration("yaw"),
                  ],
        parameters=[{"use_sim_time": use_sim_time}],
        output='screen',
        condition=IfCondition(use_simulator)
  )

# -J FR_thigh_joint 1.0 -J FL_thigh_joint 1.0 -J RR_thigh_joint 0.7 -J RL_thigh_joint 0.7"


  # Fix up the robot's ground truth to publish w.r.t. world
  # by default it is published w.r.t. the world's name, rather than "world"
  ground_truth_node = Node(
        package="champ_gazebo",
        executable="republish_ground_truth",
        name="republish_ground_truth",
        output="screen",
        parameters=[{"robot_pose_topic": "/model/go2/pose", "fixed_frame": "world", "robot_frame": LaunchConfiguration("robot_base_link")}]
  )


  load_joint_state_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        name="start_joint_state_broadcaster",
        output='screen'
  )


  load_joint_trajectory_controller = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_trajectory_controller", "-c", "/controller_manager"],
        name="start_joint_trajectory_controller",
        output='screen',
  )



  odom_republish_node = Node(
        package='champ_gazebo',
        executable='helper_publish_base_pose',
        output='screen',
  )

  # Start quadruped controller
  launch_quadruped_controller = IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('champ_bringup'), 'launch', 'go2_quadruped_controller.launch.py'])
  )

  stand_up = OpaqueFunction(function=evaluate_pose)

  return LaunchDescription(
    launch_args +
    [
      SetParameter(name='use_sim_time', value=True),
      bridge,
      spawn_entity_to_gazebo_node,
      ground_truth_node,
      RegisterEventHandler(
          event_handler=OnProcessExit(
              target_action=spawn_entity_to_gazebo_node,
              on_exit=[load_joint_state_controller],
          )
      ),
      RegisterEventHandler(
          event_handler=OnProcessExit(
              target_action=load_joint_state_controller,
              on_exit=[load_joint_trajectory_controller],
          )
      ),
      RegisterEventHandler(
          event_handler=OnProcessExit(
              target_action=load_joint_trajectory_controller,
              on_exit=[launch_quadruped_controller], #, TimerAction(period=LaunchConfiguration("robot_up"), actions=[stand_up]) ],
          ),
          condition=IfCondition(LaunchConfiguration("start_quadruped_controller"))
      ),
      odom_republish_node
    ])
