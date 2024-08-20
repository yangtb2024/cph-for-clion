# Description

## Overview

`cph-for-clion` is a toolset designed to automate the setup and testing of competitive programming problems, specifically tailored for CLion users. It seamlessly integrates with the Competitive Companion browser extension to fetch problem statements and test cases, and provides an efficient workflow for solving and testing problems within the CLion IDE.

## Key Features

- **Automatic Project Setup**: Automatically creates a new project directory with the necessary files, including a `main.cpp` template filled with problem details such as time and memory limits.
- **Seamless Integration with Competitive Companion**: Easily fetch problem data from popular competitive programming platforms using the Competitive Companion extension.
- **Automated Testing**: `run_tests.py` compiles and runs your solution against provided test cases, checking for correctness and enforcing time and memory limits.
- **Code Change Detection**: Detects changes in your `main.cpp` file, skipping unnecessary recompilation if the code remains unchanged, thus saving time during the testing phase.
- **CLion External Tools Support**: Configure `cph-for-clion` as an External Tool in CLion to directly access its functionalities from within the IDE.

## Benefits

- **Efficiency**: Automates repetitive tasks in the competitive programming workflow, allowing you to focus on solving problems.
- **Reliability**: Ensures that your solutions are tested under real contest conditions with enforced time and memory limits.
- **Integration**: Designed to work seamlessly with CLion, providing a smooth experience for developers who prefer using this powerful IDE.

## Who Should Use This Tool?

- **Competitive Programmers**: Ideal for those who participate in coding contests and need a streamlined workflow for problem-solving.
- **CLion Users**: Perfect for developers who use CLion as their primary IDE and want to leverage its powerful features for competitive programming.

## How It Works

1. **Setup**: Use `cp-setup.py` to fetch problem data and set up your project directory.
2. **Coding**: Implement your solution in `main.cpp`.
3. **Testing**: Use `run_tests.py` to compile and test your solution against the provided test cases, ensuring it meets all the constraints.

## Getting Started

To get started with `cph-for-clion`, refer to the [README.md](README.md) for detailed installation and configuration instructions.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for more details.
