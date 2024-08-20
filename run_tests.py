import os
import subprocess
import sys
import logging
import time
import ctypes
from ctypes import wintypes

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

# Windows API constants
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x100

# 定义 PROCESS_MEMORY_COUNTERS 结构
class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]

# 函数来获取进程的内存使用信息
def get_memory_usage(process_handle):
    counters = PROCESS_MEMORY_COUNTERS()
    ctypes.windll.psapi.GetProcessMemoryInfo(process_handle, ctypes.byref(counters), ctypes.sizeof(counters))
    return counters.PeakWorkingSetSize

class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    class _BasicLimitInformation(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", wintypes.LARGE_INTEGER),
            ("PerJobUserTimeLimit", wintypes.LARGE_INTEGER),
            ("LimitFlags", wintypes.DWORD),
            ("MinimumWorkingSetSize", ctypes.POINTER(ctypes.c_size_t)),
            ("MaximumWorkingSetSize", ctypes.POINTER(ctypes.c_size_t)),
            ("ActiveProcessLimit", wintypes.DWORD),
            ("Affinity", ctypes.c_void_p),  # 使用 c_void_p 代替 ULONG_PTR
            ("PriorityClass", wintypes.DWORD),
            ("SchedulingClass", wintypes.DWORD)
        ]
    _fields_ = [
        ("BasicLimitInformation", _BasicLimitInformation),
        ("IoInfo", wintypes.LARGE_INTEGER * 2),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]

def create_job_with_memory_limit(memory_limit_mb):
    job = ctypes.windll.kernel32.CreateJobObjectW(None, None)
    limit_info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
    limit_info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_PROCESS_MEMORY
    limit_info.ProcessMemoryLimit = memory_limit_mb * 1024 * 1024
    ctypes.windll.kernel32.SetInformationJobObject(
        job,
        9,  # JobObjectExtendedLimitInformation
        ctypes.byref(limit_info),
        ctypes.sizeof(limit_info)
    )
    return job

def assign_process_to_job(process, job):
    ctypes.windll.kernel32.AssignProcessToJobObject(job, process._handle)

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
def run_test(input_file, output_file, test_number, project_dir, time_limit, memory_limit):
    print(SEPARATOR)
    print(f"Running Test {test_number}:")

    with open(input_file, 'r') as f:
        input_data = f.read()

    start_time = time.time()

    try:
        job = create_job_with_memory_limit(memory_limit)

        with subprocess.Popen([os.path.join(project_dir, "solution")],
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True) as process:
            assign_process_to_job(process, job)

            try:
                stdout, _ = process.communicate(input=input_data, timeout=time_limit)
                end_time = time.time()

                elapsed_time = end_time - start_time

                # 获取内存使用情况
                peak_memory = get_memory_usage(process._handle) / (1024 * 1024)  # 转换为MB

                # 检查内存是否超过限制
                if peak_memory > memory_limit:
                    print(RED + f"Test {test_number}: Memory Limit Exceeded" + RESET)
                    print(f"Time: {elapsed_time:.3f} seconds")
                    print(f"Memory: {peak_memory:.3f} MB (Limit: {memory_limit} MB)")
                    logging.warning(f"Test {test_number}: Memory Limit Exceeded")
                    logging.info(f"Time: {elapsed_time:.3f} seconds")
                    logging.info(f"Memory: {peak_memory:.3f} MB (Limit: {memory_limit} MB)")
                    print(RED + "M" + RESET, end="")  # 输出一个红色的M，表示内存超限
                    sys.stdout.flush()
                    return False

                program_output = stdout.strip()  # 去除首尾空白字符

                # 读取期望输出
                with open(output_file, 'r') as f:
                    expected_output = f.read().strip()  # 去除首尾空白字符

                # 比较程序输出和期望输出
                if program_output == expected_output:
                    print(GREEN + f"Test {test_number}: Passed" + RESET)
                    print(f"Time: {elapsed_time:.3f} seconds")
                    print(f"Memory: {peak_memory:.3f} MB")
                    logging.info(f"Test {test_number}: Passed")
                    logging.info(f"Time: {elapsed_time:.3f} seconds")
                    logging.info(f"Memory: {peak_memory:.3f} MB")
                    print(GREEN + "." + RESET, end="")  # 输出一个绿色的点，表示测试通过
                    sys.stdout.flush()
                    return True
                else:
                    print(RED + f"Test {test_number}: Failed" + RESET)
                    print(f"Time: {elapsed_time:.3f} seconds")
                    print(f"Memory: {peak_memory:.3f} MB")
                    print(f"Expected:\n{expected_output}")
                    print(f"Got:\n{program_output}")
                    logging.info(f"Test {test_number}: Failed")
                    logging.info(f"Time: {elapsed_time:.3f} seconds")
                    logging.info(f"Memory: {peak_memory:.3f} MB")
                    logging.info(f"Expected:\n{expected_output}")
                    logging.info(f"Got:\n{program_output}")
                    print(RED + "x" + RESET, end="")  # 输出一个红色的x，表示测试失败
                    sys.stdout.flush()
                    return False

            except subprocess.TimeoutExpired:
                process.kill()  # 终止子进程
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(YELLOW + f"Test {test_number}: Time Limit Exceeded" + RESET)
                print(f"Time: {elapsed_time:.3f} seconds")
                logging.warning(f"Test {test_number}: Time Limit Exceeded")
                logging.info(f"Time: {elapsed_time:.3f} seconds")
                print(YELLOW + "!" + RESET, end="")  # 输出一个黄色的!，表示超时
                sys.stdout.flush()
                return False

    except subprocess.CalledProcessError:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(RED + "An error occurred during test execution." + RESET)
        print(f"Time: {elapsed_time:.3f} seconds")
        logging.error("An error occurred during test execution.")
        logging.info(f"Time: {elapsed_time:.3f} seconds")
        print(RED + "x" + RESET, end="")  # 输出一个红色的x，表示发生错误
        sys.stdout.flush()
        return False

# 运行所有测试用例
def run_all_tests(project_dir):
    compile_cpp(project_dir)

    time_limit, memory_limit = read_limits(project_dir)  # 读取时间和内存限制

    test_files = [f for f in os.listdir(project_dir) if f.startswith('input') and f.endswith('.txt')]
    test_files.sort()

    passed = 0
    total = len(test_files)

    for input_file in test_files:
        test_number = input_file[5:-4]  # 提取测试编号
        output_file = f"output{test_number}.txt"
        if run_test(os.path.join(project_dir, input_file), os.path.join(project_dir, output_file), test_number, project_dir, time_limit, memory_limit):
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
