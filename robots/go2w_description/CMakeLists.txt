cmake_minimum_required(VERSION 3.16.3)

project(go2w_description)

find_package(ament_cmake REQUIRED)

set(dependencies
  launch
  robot_state_publisher
  joint_state_publisher_gui
  rviz2
)

foreach(dependency IN ITEMS ${DEPS})
  find_package(${dependency} REQUIRED)
endforeach()

install(DIRECTORY config launch dae urdf
        DESTINATION share/${PROJECT_NAME}
)

ament_package()
