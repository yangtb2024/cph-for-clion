import os
import subprocess
import sys
import logging
import time
import ctypes
import hashlib
from ctypes import wintypes

LATEST_PROBLEM_FILE = "latest_problem.txt"  # 保存最近题目名称的文件
LOG_FILE = "run_tests.log"  # 日志文件名
LAST_HASH_FILE = "last_hash.txt"  # 保存上次编译的哈希值的文件

# 配置标准输出为 UTF-8 编码
sys.stdout.reconfigure(encoding='utf-8')

# 配置日志记录，仅记录到文件，并确保使用 UTF-8 编码
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s', encoding='utf-8')

# ANSI 转义序列定义颜色
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BLUE = "\033[94m"
RESET = "\033[0m"

# 单条分割线
SEPARATOR = BLUE + "-" * 60 + RESET

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

# 计算文件的哈希值
def calculate_file_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

# 读取时间和空间限制
def read_limits(project_dir):
    limits_file = os.path.join(project_dir, 'limits.txt')
    time_limit = 1  # 默认1秒
    memory_limit = 64  # 默认64MB

    if os.path.exists(limits_file):
        with open(limits_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('TimeLimit:'):
                    time_limit = int(line.split(':')[1].strip().replace(' ms', ''))
                elif line.startswith('MemoryLimit:'):
                    memory_limit = int(line.split(':')[1].strip().replace(' MB', ''))

    logging.info(f"Using time limit: {time_limit} ms and memory limit: {memory_limit} MB")
    return time_limit / 1000, memory_limit

# 编译 C++ 代码
def compile_cpp(project_dir):
    compile_command = f"g++ -std=c++17 -O2 -Wall {os.path.join(project_dir, 'main.cpp')} -o {os.path.join(project_dir, 'solution')}"
    print(SEPARATOR)
    print(CYAN + "Compiling..." + RESET)
    sys.stdout.flush()
    try:
        subprocess.run(compile_command, shell=True, check=True)
        logging.info("Compilation successful.")
        print(GREEN + "Compilation successful." + RESET)
    except subprocess.CalledProcessError:
        logging.error("Compilation failed.")
        print(RED + "Compilation failed." + RESET)
        sys.stdout.flush()
        sys.exit(1)

# 检查代码是否发生变化
def code_changed(project_dir):
    main_cpp_path = os.path.join(project_dir, 'main.cpp')
    current_hash = calculate_file_hash(main_cpp_path)

    if os.path.exists(LAST_HASH_FILE):
        with open(LAST_HASH_FILE, 'r', encoding='utf-8') as f:
            last_hash = f.read().strip()
        if current_hash == last_hash:
            print(GREEN + "No changes in the code since the last run. Skipping compilation." + RESET)
            logging.info("No changes in the code since the last run. Skipping compilation.")
            return False

    with open(LAST_HASH_FILE, 'w', encoding='utf-8') as f:
        f.write(current_hash)
    return True

# 运行单个测试用例
def run_test(input_file, output_file, test_number, project_dir, time_limit, memory_limit):
    print(f"{BLUE}Running Test {test_number}:{RESET}")
    sys.stdout.flush()

    with open(input_file, 'r', encoding='utf-8') as f:
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
                    print(f"{RED}Test {test_number}: Memory Limit Exceeded{RESET}")
                    print(f"{YELLOW}Time: {elapsed_time:.3f} seconds{RESET}")
                    print(f"{YELLOW}Memory: {peak_memory:.3f} MB (Limit: {memory_limit} MB){RESET}")
                    logging.warning(f"Test {test_number}: Memory Limit Exceeded")
                    logging.info(f"Time: {elapsed_time:.3f} seconds")
                    logging.info(f"Memory: {peak_memory:.3f} MB (Limit: {memory_limit} MB)")
                    sys.stdout.flush()
                    return "Memory Limit Exceeded", False

                program_output = stdout.strip()  # 去除首尾空白字符

                # 读取期望输出
                with open(output_file, 'r', encoding='utf-8') as f:
                    expected_output = f.read().strip()  # 去除首尾空白字符

                # 比较程序输出和期望输出
                if program_output == expected_output:
                    print(f"{GREEN}Test {test_number}: Passed{RESET}")
                    print(f"{YELLOW}Time: {elapsed_time:.3f} seconds{RESET}")
                    print(f"{YELLOW}Memory: {peak_memory:.3f} MB{RESET}")
                    logging.info(f"Test {test_number}: Passed")
                    logging.info(f"Time: {elapsed_time:.3f} seconds")
                    logging.info(f"Memory: {peak_memory:.3f} MB")
                    sys.stdout.flush()
                    return "Passed", True
                else:
                    print(f"{RED}Test {test_number}: Failed{RESET}")
                    print(f"{YELLOW}Time: {elapsed_time:.3f} seconds{RESET}")
                    print(f"{YELLOW}Memory: {peak_memory:.3f} MB{RESET}")
                    print(f"{RED}Expected:{RESET}\n{expected_output}")
                    print(f"{RED}Got:{RESET}\n{program_output}")
                    logging.info(f"Test {test_number}: Failed")
                    logging.info(f"Time: {elapsed_time:.3f} seconds")
                    logging.info(f"Memory: {peak_memory:.3f} MB")
                    logging.info(f"Expected:\n{expected_output}")
                    logging.info(f"Got:\n{program_output}")
                    sys.stdout.flush()
                    return "Failed", False

            except subprocess.TimeoutExpired:
                process.kill()  # 终止子进程
                end_time = time.time()
                elapsed_time = end_time - start_time
                print(f"{YELLOW}Test {test_number}: Time Limit Exceeded{RESET}")
                print(f"{YELLOW}Time: {elapsed_time:.3f} seconds{RESET}")
                logging.warning(f"Test {test_number}: Time Limit Exceeded")
                logging.info(f"Time: {elapsed_time:.3f} seconds")
                sys.stdout.flush()
                return "Time Limit Exceeded", False

    except subprocess.CalledProcessError:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"{RED}An error occurred during test execution.{RESET}")
        print(f"{YELLOW}Time: {elapsed_time:.3f} seconds{RESET}")
        logging.error("An error occurred during test execution.")
        logging.info(f"Time: {elapsed_time:.3f} seconds")
        sys.stdout.flush()
        return "Error", False

# 运行所有测试用例
def run_all_tests(project_dir):
    if code_changed(project_dir):
        compile_cpp(project_dir)

    time_limit, memory_limit = read_limits(project_dir)  # 读取时间和内存限制

    test_files = [f for f in os.listdir(project_dir) if f.startswith('input') and f.endswith('.txt')]
    test_files.sort()

    passed = 0
    total = len(test_files)

    print(SEPARATOR)
    print(f"{CYAN}Running {total} Test(s):{RESET}")
    sys.stdout.flush()

    for i, input_file in enumerate(test_files):
        test_number = input_file[5:-4]  # 提取测试编号
        output_file = f"output{test_number}.txt"
        status, result = run_test(os.path.join(project_dir, input_file), os.path.join(project_dir, output_file), test_number, project_dir, time_limit, memory_limit)
        if result:
            passed += 1
        print(f"Status: {status}")
        sys.stdout.flush()

        # 仅在两个测试之间打印分隔线
        if i < total - 1:
            print(SEPARATOR)
            sys.stdout.flush()

    summary = f"{CYAN}\nSummary: Passed {passed} out of {total} tests.{RESET}"
    logging.info(summary)
    print(summary)
    sys.stdout.flush()

def get_latest_problem_directory():
    if os.path.exists(LATEST_PROBLEM_FILE):
        with open(LATEST_PROBLEM_FILE, 'r', encoding='utf-8') as f:
            problem_name = f.read().strip()
        logging.info(f"Latest problem directory is '{problem_name}'")
        print(f"{CYAN}Latest problem directory is '{problem_name}'{RESET}")
        sys.stdout.flush()
        return problem_name
    else:
        logging.error(f"{LATEST_PROBLEM_FILE} not found.")
        print(f"{RED}Error: {LATEST_PROBLEM_FILE} not found.{RESET}")
        sys.stdout.flush()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) == 2:
        project_directory = sys.argv[1]
    else:
        project_directory = get_latest_problem_directory()

    if not os.path.exists(project_directory):
        logging.error(f"The directory '{project_directory}' does not exist.")
        print(f"{RED}Error: The directory '{project_directory}' does not exist.{RESET}")
        sys.stdout.flush()
        sys.exit(1)

    run_all_tests(project_directory)

    # 确保在所有测试完成后终止 solution.exe 进程，并静默处理输出，避免乱码
    subprocess.call(['taskkill', '/f', '/im', 'solution.exe'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
