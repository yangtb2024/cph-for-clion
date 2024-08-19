import sys
import json
import os
import logging
import http.server
import socketserver

PORT = 10043  # Competitive Companion 默认使用的端口
LATEST_PROBLEM_FILE = "latest_problem.txt"  # 用于保存最近的题目名称
LOG_FILE = "cp_setup.log"  # 日志文件名

# 配置日志记录
logging.basicConfig(filename=LOG_FILE, level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class CompetitiveCompanionHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        self.send_response(200)
        self.end_headers()

        data = json.loads(post_data.decode('utf-8'))
        process_data(data)

def process_data(data):
    try:
        problem_name = data.get('name', 'Unknown Problem').replace(' ', '_')
        problem_url = data.get('url', 'No URL provided')
        time_limit = data.get('timeLimit', 'Unknown')
        memory_limit = data.get('memoryLimit', 'Unknown')

        # 创建新的项目目录
        project_dir = problem_name
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)
            logging.info(f"Created project directory: {project_dir}")
        else:
            logging.info(f"Project directory already exists: {project_dir}")

        # 保存最近的题目名称到文件
        with open(LATEST_PROBLEM_FILE, 'w') as f:
            f.write(problem_name)
        logging.info(f"Saved latest problem name to {LATEST_PROBLEM_FILE}")

        # 保存时间和空间限制到文件
        with open(os.path.join(project_dir, 'limits.txt'), 'w') as f:
            f.write(f"TimeLimit: {time_limit}\n")
            f.write(f"MemoryLimit: {memory_limit}\n")
        logging.info(f"Saved limits to {os.path.join(project_dir, 'limits.txt')}")

        # 生成 C++ 代码模板并写入 main.cpp
        code_template = f"""// Problem: {problem_name}
// URL: {problem_url}
// Time Limit: {time_limit} ms
// Memory Limit: {memory_limit} MB

#include <bits/stdc++.h>

#define rep(i, l, r) for(int i = l; i <= r; i++)
#define per(i, l, r) for(int i = r; i >= l; i--)

using namespace std;

int main() {{
    #ifdef LOCAL
    freopen("task.in", "r", stdin);
    freopen("task.out", "w", stdout);
    freopen("task.err", "w", stderr);
    #endif

    return 0;
}}
"""
        with open(os.path.join(project_dir, 'main.cpp'), 'w') as f:
            f.write(code_template)
        logging.info(f"Code template for '{problem_name}' written to {os.path.join(project_dir, 'main.cpp')}")

        # 生成测试用例文件
        if 'tests' in data:
            for i, test in enumerate(data['tests'], 1):
                with open(os.path.join(project_dir, f'input{i}.txt'), 'w') as f:
                    f.write(test.get('input', ''))
                with open(os.path.join(project_dir, f'output{i}.txt'), 'w') as f:
                    f.write(test.get('output', ''))
                logging.info(f"Sample test case {i} written to {os.path.join(project_dir, f'input{i}.txt')} and {os.path.join(project_dir, f'output{i}.txt')}")

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}", exc_info=True)

def main():
    logging.info("Starting CompetitiveCompanionHandler server.")
    with socketserver.TCPServer(("", PORT), CompetitiveCompanionHandler) as httpd:
        logging.info(f"Serving at port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    main()
