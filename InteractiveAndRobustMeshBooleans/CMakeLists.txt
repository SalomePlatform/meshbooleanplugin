cmake_minimum_required(VERSION 3.12)
project(IRMB)

execute_process(
  COMMAND ${CMAKE_CURRENT_SOURCE_DIR}/compile_IRMB.sh
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    RESULT_VARIABLE script_result
)
