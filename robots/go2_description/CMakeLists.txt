cmake_minimum_required(VERSION 3.16.3)

project(go2_description)

find_package(ament_cmake REQUIRED)

set(dependencies
  rviz2
  robot_state_publisher
  joint_state_publisher_gui
  ros_gz_sim
)

foreach(dependency IN ITEMS ${DEPS})
  find_package(${dependency} REQUIRED)
endforeach()

install(DIRECTORY config launch meshes urdf dae worlds
        DESTINATION share/${PROJECT_NAME}
)

ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/${PROJECT_NAME}.dsv.in")

ament_package()
