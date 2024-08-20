import sys
import json
import os
import http.server
import socketserver

PORT = 10043  # Competitive Companion 默认使用的端口

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
        problem_name = data.get('name', 'Unknown Problem')
        problem_url = data.get('url', 'No URL provided')
        time_limit = data.get('timeLimit', 'Unknown')
        memory_limit = data.get('memoryLimit', 'Unknown')

        # 创建子文件夹
        project_dir = problem_name.replace(' ', '_')
        if not os.path.exists(project_dir):
            os.makedirs(project_dir)

        # 处理内存限制的单位
        if isinstance(memory_limit, str):
            if 'GB' in memory_limit.upper():
                memory_limit = int(float(memory_limit.split()[0]) * 1024)  # 转换 GB 为 MB
            elif 'MB' in memory_limit.upper():
                memory_limit = int(float(memory_limit.split()[0]))
            else:
                memory_limit = int(float(memory_limit))  # 假设单位为 MB 或直接是数值
        elif isinstance(memory_limit, (int, float)):
            memory_limit = int(memory_limit)  # 处理没有单位的情况，假设为 MB
        else:
            memory_limit = 'Unknown'

        code_template = f"""// Problem: {problem_name}
// URL: {problem_url}
// Time Limit: {time_limit} milliseconds
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

        # 写入 main.cpp 文件
        with open(os.path.join(project_dir, 'main.cpp'), 'w') as f:
            f.write(code_template)

        print(f"Code template for '{problem_name}' has been written to {project_dir}/main.cpp")

        if 'tests' in data:
            for i, test in enumerate(data['tests'], 1):
                with open(os.path.join(project_dir, f'input{i}.txt'), 'w') as f:
                    f.write(test.get('input', ''))
                with open(os.path.join(project_dir, f'output{i}.txt'), 'w') as f:
                    f.write(test.get('output', ''))
                print(f"Sample test case {i} written to {project_dir}/input{i}.txt and {project_dir}/output{i}.txt")

        # 将内存和时间限制保存到 limits.txt
        with open(os.path.join(project_dir, 'limits.txt'), 'w') as f:
            f.write(f"TimeLimit: {time_limit}\n")
            f.write(f"MemoryLimit: {memory_limit}\n")
        print(f"Limits for '{problem_name}' have been written to {project_dir}/limits.txt")

        # 保存最近的题目名称到文件
        with open('latest_problem.txt', 'w') as f:
            f.write(project_dir)
        print(f"Latest problem directory '{project_dir}' has been saved to latest_problem.txt")

    except Exception as e:
        print(f"An error occurred: {str(e)}", file=sys.stderr)

def main():
    with socketserver.TCPServer(("", PORT), CompetitiveCompanionHandler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    main()
