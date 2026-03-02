cmake_minimum_required(VERSION 3.20) # VERSION 4.1 doesn't exist yet! 3.20 is standard.
project(suply_chain_optimization_algorithm_comparison)

set(CMAKE_CXX_STANDARD 20)

# 1. Look for Raylib on your system
find_package(raylib REQUIRED)

# 2. Add your executable
add_executable(suply_chain_optimization_algorithm_comparison main.cpp)

# 3. Link the libraries (The "Muscle")
# On Arch, Raylib needs these specific system libraries to talk to your GPU
target_link_libraries(suply_chain_optimization_algorithm_comparison
        PRIVATE
        raylib
        GL
        m
        pthread
        dl
        rt
        X11
)