cmake_minimum_required(VERSION 3.30)
project(simulate-browser LANGUAGES CXX)
set(CMAKE_CXX_STANDARD 20)

add_library(post_process
  STATIC
  ${CMAKE_SOURCE_DIR}/post_process.cpp
)

add_library(download
  STATIC
  ${CMAKE_SOURCE_DIR}/download.cpp
)
target_link_libraries(download curl)

add_library(main_lib
  STATIC
  ${CMAKE_SOURCE_DIR}/main_lib.cpp
)
target_link_libraries(main_lib curl)

add_executable(simulate-browser)
target_sources(simulate-browser
  PUBLIC
  ${CMAKE_SOURCE_DIR}/main.cpp
)
target_link_libraries(simulate-browser post_process download main_lib)

include(CTest)
add_executable(simulate-browser_test test_simulate_browser.cpp)
target_link_libraries(simulate-browser_test PUBLIC gtest post_process download main_lib)
add_test(NAME MainTest COMMAND simulate-browser_test)
enable_testing()
