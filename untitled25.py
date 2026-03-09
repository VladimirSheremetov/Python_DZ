# -*- coding: utf-8 -*-
import http.server
import json
import os
import socketserver
from urllib.parse import urlparse

PORT = 8000
DATA_FILE = "tasks.txt"

tasks = []
next_id = 1


def save_tasks_to_file():
    """Save tasks to file"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            data = {
                'tasks': tasks,
                'next_id': next_id
            }
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving to file: {e}")


def load_tasks_from_file():
    """Load tasks from file"""
    global tasks, next_id
    
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                tasks = data.get('tasks', [])
                next_id = data.get('next_id', 1)
                print(f"Loaded {len(tasks)} tasks from file")
        except Exception as e:
            print(f"Error loading from file: {e}")
            tasks = []
            next_id = 1


class TaskHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler for todo list management"""
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/tasks":
            self.handle_get_tasks()
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urlparse(self.path)
        
        if parsed_path.path == "/tasks":
            self.handle_create_task()
        elif parsed_path.path.startswith("/tasks/") and parsed_path.path.endswith("/complete"):
            self.handle_complete_task()
        else:
            self.send_response(404)
            self.end_headers()
    
    def handle_get_tasks(self):
        """Return list of all tasks"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(tasks).encode())
    
    def handle_create_task(self):
        """Create new task"""
        global next_id
        
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            task_data = json.loads(post_data.decode('utf-8'))
            
            if 'title' not in task_data or 'priority' not in task_data:
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Missing required fields"}).encode())
                return
            
            new_task = {
                'id': next_id,
                'title': task_data['title'],
                'priority': task_data['priority'],
                'isDone': False
            }
            
            tasks.append(new_task)
            next_id += 1
            
            save_tasks_to_file()
            
            self.send_response(201)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(new_task).encode())
            
        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
    
    def handle_complete_task(self):
        """Mark task as completed"""
        path_parts = self.path.split('/')
        if len(path_parts) >= 3:
            try:
                task_id = int(path_parts[2])
                
                for task in tasks:
                    if task['id'] == task_id:
                        task['isDone'] = True
                        save_tasks_to_file()
                        self.send_response(200)
                        self.end_headers()
                        return
                
                self.send_response(404)
                self.end_headers()
            except ValueError:
                self.send_response(404)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()


def run_server():
    """Run HTTP server"""
    load_tasks_from_file()
    
    handler = TaskHandler
    socketserver.TCPServer.allow_reuse_address = True
    
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Server started on port {PORT}")
        print(f"Available endpoints:")
        print(f"  GET  /tasks - get all tasks")
        print(f"  POST /tasks - create task")
        print(f"  POST /tasks/<id>/complete - mark task as done")
        print(f"Data saved to file: {DATA_FILE}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")
            save_tasks_to_file()


if __name__ == "__main__":
    run_server()
