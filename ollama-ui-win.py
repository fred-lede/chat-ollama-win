import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import requests
import configparser
import threading
import json
import time
import logging
from PIL import Image, ImageTk
import base64  # 新增，用于编码图像数据

# import ollama  # 已移除，因为不再使用 ollama 库

# 读取配置
config = configparser.ConfigParser()
config.read('config.ini')

# 配置日志
logging.basicConfig(filename='ollama_gui.log', level=logging.DEBUG, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

try:
    OLLAMA_SERVICE_URL = config['Server']['Address']
    OLLAMA_SERVICE_PORT = config['Server']['Port']
except KeyError as e:
    raise KeyError(f"Missing configuration for {e}")

# Database setup
myDATABASE = 'ollama_QA.db'
smallFrame ='1000x900'
bigFrame = '1000x1050'

class OllamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Chat UI for Windows Ver.02")
        self.root.geometry(smallFrame)
        self.service_url = f"http://{OLLAMA_SERVICE_URL}:{OLLAMA_SERVICE_PORT}"
        self.uploaded_image_data = None
        self.initialize_database()
        self.create_widgets()
        self.configure_styles()  # 初始化样式

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use('default')  # 使用默认主题

        # 定义 "Ask.TButton" 样式
        style.configure("Ask.TButton",
                        foreground="white",  # 文字颜色
                        background="#28a745",  # 背景颜色 (绿色)
                        font=('Helvetica', 12, 'bold'))
        
        # 定义 "Image Upload Button" 样式                
        style.configure("ImageUpload.TButton",
                        foreground="white",  # 文字颜色
                        background="#FFA500",  # 背景颜色 (深橘黄)
                        font=('Helvetica', 12, 'bold'))

        # 定义 "Other.TButton" 样式
        style.configure("Other.TButton",
                        foreground="black",  # 文字颜色
                        font=('Helvetica', 10, ''))

        # 设置按下和活动状态时的颜色
        style.map("Ask.TButton",
                  foreground=[('pressed', 'white'), ('active', 'white')],
                  background=[('pressed', '#218838'), ('active', '#218838')])
                  
        style.map("ImageUpload.TButton",
                  foreground=[('pressed', 'white'), ('active', 'white')],
                  background=[('pressed', '#FF8C00'), ('active', '#FF8C00')])

    def initialize_database(self):
        conn = sqlite3.connect(myDATABASE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model TEXT NOT NULL,
                topic TEXT NOT NULL,
                question TEXT NOT NULL,
                answer TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def create_widgets(self):
        # Ollama Server
        tk.Label(self.root, text="Server:", font=('Helvetica', 12)).grid(row=0, column=0, padx=10, pady=10, sticky='w')
        tk.Label(self.root, text=self.service_url, fg='blue', font=('Helvetica', 12)).grid(row=0, column=1, padx=10, pady=10, sticky='w')

        # Model Selection
        self.model_var = tk.StringVar()
        tk.Label(self.root, text="Model:", font=('Helvetica', 12)).grid(row=1, column=0, padx=10, pady=10, sticky='w')
        self.model_menu = ttk.OptionMenu(self.root, self.model_var, 'Select Model', *self.get_models(), command=self.select_model)
        self.model_menu.grid(row=1, column=1, padx=10, pady=10, sticky='w')

        # 手动选择是否支持 Vision
        self.vision_var = tk.BooleanVar()
        self.vision_checkbutton = tk.Checkbutton(self.root, text="Support Vision (Image Upload)", variable=self.vision_var, command=self.toggle_image_upload)
        self.vision_checkbutton.grid(row=2, column=1, padx=10, pady=10, sticky='w')
        
        # Topic Entry
        tk.Label(self.root, text="Topic:", font=('Helvetica', 12)).grid(row=4, column=0, padx=10, pady=10, sticky='w')
        self.topic_entry = ttk.Entry(self.root, width=50)
        self.topic_entry.grid(row=4, column=1, padx=10, pady=10, sticky='w')
        
        # Question Text and Image Area
        tk.Label(self.root, text="Question:", font=('Helvetica', 12)).grid(row=5, column=0, padx=10, pady=10, sticky='w')
        self.question_frame = ttk.Frame(self.root)
        self.question_frame.grid(row=5, column=1, columnspan=2, padx=10, pady=10, sticky='ew')
        self.image_label = tk.Label(self.question_frame, bg="grey")  # 背景色暂时设为灰色以便可视化
        self.image_label.grid(row=0, column=0, padx=10, pady=10)
        self.image_label.grid_remove()
        self.question_text = tk.Text(self.question_frame, height=10, width=50)
        self.question_text.grid(row=0, column=1, padx=5, pady=5)

        # Answer Text
        tk.Label(self.root, text="Answer:", font=('Helvetica', 12)).grid(row=6, column=0, padx=10, pady=10, sticky='w')
        self.answer_frame = ttk.Frame(self.root)
        self.answer_frame.grid(row=6, column=1, columnspan=2, padx=10, pady=10, sticky='ew')
        self.answer_label = tk.Label(self.answer_frame, bg="grey")  # 背景色暂时设为灰色以便可视化
        self.answer_label.grid(row=0, column=0, padx=10, pady=10)
        self.answer_label.grid_remove()
        self.answer_entry = tk.Text(self.answer_frame, height=10, width=110)
        self.answer_entry.grid(row=0, column=1, padx=5, pady=5)

        # Buttons Frame
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=7, column=0, columnspan=2, pady=20)

        ttk.Button(button_frame, text="Load", style="Other.TButton", command=self.load_data).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Edit", style="Other.TButton", command=self.edit_data).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Delete", style="Other.TButton", command=self.delete_data).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Search", style="Other.TButton", command=self.search_data).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="Export to Text", style="Other.TButton", command=self.export_to_text).grid(row=0, column=4, padx=5)
        # Image Upload Button (hidden by default)
        self.upload_image_button = ttk.Button(button_frame, text="Upload Image", style="ImageUpload.TButton", command=self.upload_image)
        self.upload_image_button.grid(row=0, column=5, padx=5)
        self.upload_image_button.grid_remove()
        ttk.Button(button_frame, text="Ask", style="Ask.TButton", command=self.ask_question).grid(row=0, column=6, padx=5)
        

        # Treeview for displaying data
        self.tree = ttk.Treeview(self.root, columns=("ID", "Model", "Topic", "Question", "Answer", "Timestamp"), show='headings')
        self.tree.heading("ID", text="ID")
        self.tree.heading("Model", text="Model")
        self.tree.heading("Topic", text="Topic")
        self.tree.heading("Question", text="Question")
        self.tree.heading("Answer", text="Answer")
        self.tree.heading("Timestamp", text="Timestamp")
        self.tree.column("ID", width=50)
        self.tree.column("Model", width=100)
        self.tree.column("Topic", width=150)
        self.tree.column("Question", width=250)
        self.tree.column("Answer", width=250)
        self.tree.column("Timestamp", width=150)
        self.tree.grid(row=8, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')

        # Configure grid to make treeview expandable
        self.root.grid_rowconfigure(6, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        # 添加进度条
        self.progress = ttk.Progressbar(self.root, orient='horizontal', mode='indeterminate')
        self.progress.grid(row=9, column=0, columnspan=2, padx=10, pady=10, sticky='we')

        # 作者
        tk.Label(self.root, text="e-mail: fred.yt.wang@gmail.com", font=('Helvetica', 10)).grid(row=10, column=0, columnspan=2, padx=10, pady=10, sticky='w')

        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def get_models(self):
        try:
            response = requests.get(f"{self.service_url}/v1/models")
            response.raise_for_status()
            data = response.json()

            if isinstance(data, dict) and data.get("object") == "list" and "data" in data:
                models = data["data"]
                return [model["id"] for model in models]
            elif isinstance(data, list):
                return data
            else:
                raise ValueError("Unexpected response format")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Failed to retrieve models: {e}")
            print(f"Error details: {e}")
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
            print(f"ValueError: {ve}")
        return []

    def select_model(self, value):
        print(f'Selected model: {value}')

    def toggle_image_upload(self):
        if self.vision_var.get():  # 如果手动选择支持 Vision
            self.upload_image_button.grid()
            self.image_label.grid()
            if self.uploaded_image_data:
                self.root.geometry(bigFrame)
            else:
                self.root.geometry(smallFrame)
        else:
            self.upload_image_button.grid_remove()
            self.image_label.grid_remove()
            self.root.geometry(smallFrame)
    
    def upload_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp *.gif"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, 'rb') as img_file:
                self.uploaded_image_data = img_file.read()
            self.display_image(file_path)
            
    def display_image(self, file_path):
        self.root.geometry(bigFrame)
        img = Image.open(file_path)
        img.thumbnail((400, 300))  # Resize image to fit in the UI
        img = ImageTk.PhotoImage(img)
        self.image_label.config(image=img)
        self.image_label.image = img

    def ask_question(self):
        selected_model = self.model_var.get()
        topic = self.topic_entry.get().strip()
        question = self.question_text.get("1.0", tk.END).strip()

        if not selected_model or selected_model == 'Select Model':
            messagebox.showwarning("Input Error", "Please select a model.")
            return

        if not question:
            messagebox.showwarning("Input Error", "Question field cannot be empty.")
            return

        # 启动新线程处理请求
        thread = threading.Thread(target=self._ask_question_thread, args=(selected_model, topic, question))
        thread.start()

    def _ask_question_thread(self, selected_model, topic, question):
        logging.info(f"Sending question to model {selected_model}: {question}")
        self.root.after(0, self.progress.start)  # 启动进度条
        self.root.after(0, self.set_cursor_wait)  # 设置游标为等待状态

        try:
            payload = {
                "model": selected_model,
                "messages": [
                    {
                        "role": "user",
                        "content": question
                    }
                ]
            }

            if self.vision_var.get() and self.uploaded_image_data:
                # 如果选择了 Vision 且上传了图片，添加 images 字段
                # 假设 API 需要 Base64 编码的图像数据
                encoded_image = base64.b64encode(self.uploaded_image_data).decode('utf-8')
                payload["messages"][0]["images"] = [encoded_image]

            headers = {"Content-Type": "application/json"}
            response = requests.post(f"{self.service_url}/api/chat", json=payload, headers=headers, stream=True)
            response.raise_for_status()

            collected_content = []
            for line in response.iter_lines():
                if line:
                    data = json.loads(line.decode('utf-8'))
                    if "error" in data:
                        raise ValueError(data["error"])
                    content = data.get('message', {}).get('content', '')
                    if content:
                        collected_content.append(content)
                    if data.get('done', False):
                        break
            answer = ''.join(collected_content).strip()

            # 更新 GUI 必须在主线程中进行
            self.root.after(0, self.display_answer, answer)

            # 自动保存问答对到数据库
            self.root.after(0, self.save_question_answer, selected_model, topic, question, answer)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to send question: {e}")
            logging.error(f"RequestException: {e}")
        finally:
            self.root.after(0, self.reset_cursor)  # 恢复游标
            self.root.after(0, self.progress.stop)  # 停止进度条

    def set_cursor_wait(self):
        self.root.config(cursor="wait")
        self.root.update()

    def display_answer(self, answer):
        self.answer_entry.delete("1.0", tk.END)
        self.answer_entry.insert(tk.END, answer)

    def reset_cursor(self):
        self.root.config(cursor="")
        self.root.update()

    def save_question_answer(self, model, topic, question, answer):
        try:
            conn = sqlite3.connect(myDATABASE)
            c = conn.cursor()
            c.execute("INSERT INTO questions (model, topic, question, answer) VALUES (?, ?, ?, ?)", (model, topic, question, answer))
            conn.commit()
            conn.close()
            self.load_data()  # 刷新数据展示
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save question and answer: {e}")
            logging.error(f"Database Error: {e}")

    def load_data(self):
        try:
            conn = sqlite3.connect(myDATABASE)
            c = conn.cursor()
            c.execute("SELECT * FROM questions ORDER BY ID DESC")
            rows = c.fetchall()
            conn.close()
            
            # 清除现有的树状视图数据
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 插入新的数据
            for row in rows:
                self.tree.insert('', tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            logging.error(f"Database Error: {e}")

    def on_tree_select(self, event):
        selected_item = self.tree.focus()
        if selected_item:
            values = self.tree.item(selected_item, 'values')
            if values:
                _, model, topic, question, answer, timestamp = values
                self.model_var.set(model)  # 设置选中的模型
                self.topic_entry.delete(0, tk.END)
                self.topic_entry.insert(0, topic)
                self.question_text.delete("1.0", tk.END)
                self.question_text.insert(tk.END, question)
                self.answer_entry.delete("1.0", tk.END)
                self.answer_entry.insert(tk.END, answer)

    def edit_data(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a record to edit.")
            return
        
        values = self.tree.item(selected_item, 'values')
        if not values:
            messagebox.showwarning("Selection Error", "Selected item has no data.")
            return
        
        record_id, model, topic, question, answer, timestamp = values
        
        new_model = self.model_var.get().strip()
        new_topic = self.topic_entry.get().strip()
        new_question = self.question_text.get("1.0", tk.END).strip()
        new_answer = self.answer_entry.get("1.0", tk.END).strip()
        
        if not new_model or new_model == 'Select Model':
            messagebox.showwarning("Input Error", "Please select a model.")
            return
        
        if not new_topic or not new_question:
            messagebox.showwarning("Input Error", "Topic and Question fields cannot be empty.")
            return
        
        try:
            conn = sqlite3.connect(myDATABASE)
            c = conn.cursor()
            c.execute("UPDATE questions SET model=?, topic=?, question=?, answer=? WHERE id=?", (new_model, new_topic, new_question, new_answer, record_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("Success", "Record updated successfully.")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            logging.error(f"Database Error: {e}")

    def delete_data(self):
        selected_item = self.tree.focus()
        if not selected_item:
            messagebox.showwarning("Selection Error", "Please select a record to delete.")
            return
        
        values = self.tree.item(selected_item, 'values')
        if not values:
            messagebox.showwarning("Selection Error", "Selected item has no data.")
            return
        
        record_id = values[0]
        
        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete the selected record?")
        if not confirm:
            return
        
        try:
            conn = sqlite3.connect(myDATABASE)
            c = conn.cursor()
            c.execute("DELETE FROM questions WHERE id=?", (record_id,))
            conn.commit()
            conn.close()
            self.load_data()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            logging.error(f"Database Error: {e}")

    def search_data(self):
        topic = self.topic_entry.get().strip()
        if not topic:
            messagebox.showwarning("Input Error", "Please enter a topic to search.")
            return
        
        try:
            conn = sqlite3.connect(myDATABASE)
            c = conn.cursor()
            c.execute("SELECT * FROM questions WHERE topic LIKE ?", ('%' + topic + '%',))
            rows = c.fetchall()
            conn.close()
            
            # 清除现有数据
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 插入搜索结果
            for row in rows:
                self.tree.insert('', tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            logging.error(f"Database Error: {e}")

    def export_to_text(self):
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save as"
            )
            if not file_path:
                return  # 如果用户取消操作，则退出函数

            conn = sqlite3.connect(myDATABASE)
            c = conn.cursor()
            c.execute("SELECT * FROM questions")
            rows = c.fetchall()
            conn.close()

            with open(file_path, 'w', encoding='utf-8') as f:
                for row in rows:
                    id, model, topic, question, answer, timestamp = row
                    f.write(f"ID: {id}\n")
                    f.write(f"Model: {model}\n")
                    f.write(f"Topic: {topic}\n")
                    f.write(f"Question: {question}\n")
                    f.write(f"Answer: {answer}\n")
                    f.write(f"Timestamp: {timestamp}\n")
                    f.write("-" * 50 + "\n")

            messagebox.showinfo("Success", f"Data exported successfully to {file_path}")
            logging.info(f"Data exported successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")
            logging.error(f"Export Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    gui = OllamaGUI(root)
    root.mainloop()
