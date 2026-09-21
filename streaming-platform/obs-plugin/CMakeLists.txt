cmake_minimum_required(VERSION 3.16...3.27)
project(dnd-streaming-obs-plugin VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find OBS Studio
find_package(libobs REQUIRED)
find_package(obs-frontend-api REQUIRED)

# Source files
set(SOURCES
    src/plugin-main.cpp
    src/scene-manager.cpp
    src/overlay-manager.cpp
    src/dice-roller.cpp
    src/character-display.cpp
    src/chat-overlay.cpp
    src/donation-alert.cpp
    src/stream-control.cpp
    src/settings-dialog.cpp
    src/utils.cpp
)

# Header files
set(HEADERS
    include/plugin-main.h
    include/scene-manager.h
    include/overlay-manager.h
    include/dice-roller.h
    include/character-display.h
    include/chat-overlay.h
    include/donation-alert.h
    include/stream-control.h
    include/settings-dialog.h
    include/utils.h
)

# Create plugin
add_library(dnd-streaming MODULE ${SOURCES} ${HEADERS})

# Include directories
target_include_directories(dnd-streaming PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${libobs_INCLUDE_DIRS}
    ${obs-frontend-api_INCLUDE_DIRS}
)

# Link libraries
target_link_libraries(dnd-streaming PRIVATE
    ${libobs_LIBRARIES}
    ${obs-frontend-api_LIBRARIES}
    obs-frontend-api
)

# Set plugin properties
set_target_properties(dnd-streaming PROPERTIES
    PREFIX ""
    OUTPUT_NAME "dnd-streaming"
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/rundir/$<CONFIG>/obs-plugins/64bit/"
)

# Install plugin
install(TARGETS dnd-streaming
    LIBRARY DESTINATION "obs-plugins/64bit/"
)

# Install locale files
install(DIRECTORY data/locale/
    DESTINATION "obs-plugins/dnd-streaming/locale/"
)

# Copy plugin files to OBS plugins directory on Windows
if(WIN32)
    add_custom_command(TARGET dnd-streaming POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy
        "$<TARGET_FILE:dnd-streaming>"
        "$ENV{PROGRAMFILES}/obs-studio/obs-plugins/64bit/"
    )
endif()