import os
import subprocess
import sys
import logging

LATEST_PROBLEM_FILE = "latest_problem.txt"  # 保存最近题目名称的文件
LOG_FILE = "run_tests.log"  # 日志文件名

# 配置日志记录，仅记录到文件
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# ANSI 转义序列定义颜色
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"

# 分割线
SEPARATOR = CYAN + "-" * 50 + RESET

# 读取时间和空间限制
def read_limits(project_dir):
    limits_file = os.path.join(project_dir, 'limits.txt')
    time_limit = 1  # 默认1秒
    memory_limit = 64  # 默认64MB

    if os.path.exists(limits_file):
        with open(limits_file, 'r') as f:
            for line in f:
                if line.startswith('TimeLimit:'):
                    time_limit = int(line.split(':')[1].strip())
                elif line.startswith('MemoryLimit:'):
                    memory_limit = int(line.split(':')[1].strip())

    logging.info(f"Using time limit: {time_limit} ms and memory limit: {memory_limit} MB")
    return time_limit / 1000, memory_limit

# 编译 C++ 代码
def compile_cpp(project_dir):
    compile_command = f"g++ -std=c++17 -O2 -Wall {os.path.join(project_dir, 'main.cpp')} -o {os.path.join(project_dir, 'solution')}"
    try:
        subprocess.run(compile_command, shell=True, check=True)
        logging.info("Compilation successful.")
        print(GREEN + "Compilation successful." + RESET)
    except subprocess.CalledProcessError:
        logging.error("Compilation failed.")
        print(RED + "Compilation failed." + RESET)
        sys.exit(1)

# 运行单个测试用例
def run_test(input_file, output_file, test_number, project_dir, time_limit):
    print(SEPARATOR)
    print(f"Running Test {test_number}:")

    with open(input_file, 'r') as f:
        input_data = f.read()

    try:
        result = subprocess.run([os.path.join(project_dir, "solution")], input=input_data, capture_output=True, text=True, timeout=time_limit)
        program_output = result.stdout
    except subprocess.TimeoutExpired:
        logging.warning(f"Test {test_number}: Time Limit Exceeded")
        print(YELLOW + f"Test {test_number}: Time Limit Exceeded" + RESET)
        return False

    with open(output_file, 'r') as f:
        expected_output = f.read()

    if program_output.strip() == expected_output.strip():
        logging.info(f"Test {test_number}: Passed")
        print(GREEN + f"Test {test_number}: Passed" + RESET)
        return True
    else:
        logging.info(f"Test {test_number}: Failed")
        print(RED + f"Test {test_number}: Failed" + RESET)
        print(RED + "Expected:" + RESET)
        print(expected_output)
        print(RED + "Got:" + RESET)
        print(program_output)
        return False

# 运行所有测试用例
def run_all_tests(project_dir):
    compile_cpp(project_dir)

    time_limit, _ = read_limits(project_dir)  # 读取时间限制，暂时忽略内存限制

    test_files = [f for f in os.listdir(project_dir) if f.startswith('input')]
    test_files.sort()

    passed = 0
    total = len(test_files)

    for input_file in test_files:
        test_number = input_file[5:-4]  # 提取测试编号
        output_file = f"output{test_number}.txt"
        if run_test(os.path.join(project_dir, input_file), os.path.join(project_dir, output_file), test_number, project_dir, time_limit):
            passed += 1

    logging.info(f"\nPassed {passed} out of {total} tests.")
    print(SEPARATOR)
    print(CYAN + f"\nPassed {passed} out of {total} tests." + RESET)

def get_latest_problem_directory():
    if os.path.exists(LATEST_PROBLEM_FILE):
        with open(LATEST_PROBLEM_FILE, 'r') as f:
            problem_name = f.read().strip()
        logging.info(f"Latest problem directory is '{problem_name}'")
        print(CYAN + f"Latest problem directory is '{problem_name}'" + RESET)
        return problem_name
    else:
        logging.error(f"{LATEST_PROBLEM_FILE} not found.")
        print(RED + f"Error: {LATEST_PROBLEM_FILE} not found." + RESET)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        project_directory = sys.argv[1]
    else:
        project_directory = get_latest_problem_directory()

    if not os.path.exists(project_directory):
        logging.error(f"The directory '{project_directory}' does not exist.")
        print(RED + f"Error: The directory '{project_directory}' does not exist." + RESET)
        sys.exit(1)

    run_all_tests(project_directory)
