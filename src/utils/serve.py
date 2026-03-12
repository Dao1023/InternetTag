#!/usr/bin/env python3
"""简单的HTTP服务器用于查看分析结果"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 8000
DIRECTORY = Path(__file__).parent.parent / "docs"

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # 添加CORS头以允许跨域请求
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    os.chdir(DIRECTORY)

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🚀 服务器启动成功!")
        print(f"📁 服务目录: {DIRECTORY.absolute()}")
        print(f"🌐 访问地址: http://localhost:{PORT}")
        print(f"📊 规则匹配: http://localhost:{PORT}/rule-based.html")
        print(f"🤖 聚类分析: http://localhost:{PORT}/clustering.html")
        print(f"\n按 Ctrl+C 停止服务器\n")

        # 自动打开浏览器
        webbrowser.open(f'http://localhost:{PORT}')

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\n👋 服务器已停止")
