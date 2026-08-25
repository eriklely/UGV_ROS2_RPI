cmake_minimum_required(VERSION 3.8)
project(ugv_nav)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(nav2_bringup REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

install(
  DIRECTORY launch param maps rviz config
  DESTINATION share/${PROJECT_NAME}
)

install(PROGRAMS
  scripts/gps_waypoint_follower.py
  DESTINATION lib/${PROJECT_NAME}
  RENAME gps_waypoint_follower
)

ament_package()
