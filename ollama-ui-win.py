import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import requests
import configparser
import threading
import json
import time
import logging

# 讀取配置
config = configparser.ConfigParser()
config.read('config.ini')

# 配置日誌
logging.basicConfig(filename='ollama_gui.log', level=logging.DEBUG, 
                    format='%(asctime)s:%(levelname)s:%(message)s')

try:
    OLLAMA_SERVICE_URL = config['Server']['Address']
    OLLAMA_SERVICE_PORT = config['Server']['Port']
except KeyError as e:
    raise KeyError(f"Missing configuration for {e}")
    
# Database setup
myDATABASE = 'ollama_QA.db'

class OllamaGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Chat UI for Windows Ver.01")
        self.root.geometry("1000x800")
        self.service_url = f"http://{OLLAMA_SERVICE_URL}:{OLLAMA_SERVICE_PORT}"
        # print(f"Service URL: {self.service_url}")  # 用於調試
        self.initialize_database()
        self.create_widgets()
        self.configure_styles()  # 初始化樣式

    def configure_styles(self):
        style = ttk.Style()
        style.theme_use('default')  # 使用默認主題
        
        # 定義 "Ask.TButton" 樣式
        style.configure("Ask.TButton",
                        foreground="white",  # 文字顏色
                        background="#28a745",  # 背景顏色 (綠色)
                        font=('Helvetica', 12, 'bold'))
                        
        # 定義 "Other.TButton" 樣式
        style.configure("Other.TButton",
                        foreground="black",  # 文字顏色
                        font=('Helvetica', 10, ''))

        # 設置按下和活動狀態時的顏色
        style.map("Ask.TButton",
                  foreground=[('pressed', 'white'), ('active', 'white')],
                  background=[('pressed', '#218838'), ('active', '#218838')])

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
        
        # Topic Entry
        tk.Label(self.root, text="Topic:", font=('Helvetica', 12)).grid(row=2, column=0, padx=10, pady=10, sticky='w')
        self.topic_entry = ttk.Entry(self.root, width=50)
        self.topic_entry.grid(row=2, column=1, padx=10, pady=10, sticky='w')
        
        # Question Text
        tk.Label(self.root, text="Question:", font=('Helvetica', 12)).grid(row=3, column=0, padx=10, pady=10, sticky='nw')
        self.question_text = tk.Text(self.root, height=5, width=110)
        self.question_text.grid(row=3, column=1, padx=10, pady=10, sticky='w')
        
        # Answer Text
        tk.Label(self.root, text="Answer:", font=('Helvetica', 12)).grid(row=4, column=0, padx=10, pady=10, sticky='nw')
        self.answer_entry = tk.Text(self.root, height=10, width=110)
        self.answer_entry.grid(row=4, column=1, padx=10, pady=10, sticky='w')
        
        # Buttons Frame
        button_frame = ttk.Frame(self.root)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Load", style="Other.TButton", command=self.load_data).grid(row=0, column=0, padx=5)
        ttk.Button(button_frame, text="Edit", style="Other.TButton", command=self.edit_data).grid(row=0, column=1, padx=5)
        ttk.Button(button_frame, text="Delete", style="Other.TButton", command=self.delete_data).grid(row=0, column=2, padx=5)
        ttk.Button(button_frame, text="Search", style="Other.TButton", command=self.search_data).grid(row=0, column=3, padx=5)
        ttk.Button(button_frame, text="Export to Text", style="Other.TButton", command=self.export_to_text).grid(row=0, column=4, padx=5)
        ttk.Button(button_frame, text="Ask", style="Ask.TButton", command=self.ask_question).grid(row=0, column=5, padx=5)
        
        
        
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
        self.tree.grid(row=6, column=0, columnspan=2, padx=10, pady=10, sticky='nsew')
        
        # Configure grid to make treeview expandable
        self.root.grid_rowconfigure(5, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        
        # 添加進度條
        self.progress = ttk.Progressbar(self.root, orient='horizontal', mode='indeterminate')
        self.progress.grid(row=7, column=0, columnspan=2, padx=10, pady=10, sticky='we')
        
        # 作者
        tk.Label(self.root, text="e-mail: fred.yt.wang@gmail.com", font=('Helvetica', 10)).grid(row=8, column=0, columnspan=2, padx=10, pady=10, sticky='w')
       
        
        
        self.tree.bind('<<TreeviewSelect>>', self.on_tree_select)

    def get_models(self):
        try:
            response = requests.get(f"{self.service_url}/v1/models")
            response.raise_for_status()
            data = response.json()
            # print("API Response:", data) # 用於調試，顯示後台輸出狀況
            
            if isinstance(data, dict) and data.get("object") == "list" and "data" in data:
                models = data["data"]
                return [model["id"] for model in models]
            elif isinstance(data, list):
                # 如果返回的是模型名稱的列表
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
        # 確保模型名稱正確
        # 您可以在此處添加更多處理邏輯，例如加載選定模型的相關資訊

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

        # 啟動新線程處理請求
        thread = threading.Thread(target=self._ask_question_thread, args=(selected_model, topic, question))
        thread.start()

    def _ask_question_thread(self, selected_model, topic, question, retry_count=0, max_retries=3):
        logging.info(f"Sending question to model {selected_model}: {question}")
        # 啟動進度條
        self.root.after(0, self.progress.start)
        # 設置游標為等待狀態
        self.root.after(0, self.set_cursor_wait)

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

            headers = {
                "Content-Type": "application/json"
            }
            # print(f"Sending request to {self.service_url}/api/chat with data: {payload}")  # 日誌
            response = requests.post(f"{self.service_url}/api/chat", json=payload, headers=headers, stream=True)
            response.raise_for_status()

            collected_content = []
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line.decode('utf-8'))
                        # print("Ask Response Chunk:", data)
                        # 檢查是否有錯誤字段
                        if "error" in data:
                            raise ValueError(data["error"])
                        
                        # 根據服務器回應格式解析回答
                        content = data.get('message', {}).get('content', '')
                        if content:
                            collected_content.append(content)
                        
                        if data.get('done', False):
                            # 完成接收所有內容
                            break
                    except json.JSONDecodeError as je:
                        logging.error(f"JSONDecodeError: {je}")
                        print(f"JSONDecodeError: {je}")
                        continue  # 繼續處理下一行
            answer = ''.join(collected_content).strip()

            if not answer:
                done_reason = data.get('done_reason', '')
                if done_reason == 'load' and retry_count < max_retries:
                    # 模型正在加載，等待並重試
                    print("Model is loading. Retrying in 5 seconds...")
                    logging.info("Model is loading. Retrying in 5 seconds...")
                    time.sleep(5)  # 等待5秒
                    self.root.after(0, lambda: self._ask_question_thread(selected_model, topic, question, retry_count + 1, max_retries))
                    return
                elif done_reason == 'load':
                    answer = "Model is currently loading. Please try again shortly."
                else:
                    answer = "No answer returned by the server."

            # 更新 GUI 必須在主線程中進行
            self.root.after(0, self.display_answer, answer, data)

            # 自動保存問答對到數據庫
            self.root.after(0, self.save_question_answer, selected_model, topic, question, answer)

        except requests.RequestException as e:
            self.root.after(0, messagebox.showerror, "Error", f"Failed to send question: {e}")
            print(f"Error details: {e}")
            logging.error(f"RequestException: {e}")
        except ValueError as ve:
            self.root.after(0, messagebox.showerror, "Error", f"Server Error: {ve}")
            print(f"ValueError: {ve}")
            logging.error(f"ValueError: {ve}")
        except json.JSONDecodeError as je:
            self.root.after(0, messagebox.showerror, "Error", f"JSON Decode Error: {je}")
            print(f"JSONDecodeError: {je}")
            logging.error(f"JSONDecodeError: {je}")
        finally:
            # 恢復游標
            self.root.after(0, self.reset_cursor)
            # 停止進度條
            self.root.after(0, self.progress.stop())

    def set_cursor_wait(self):
        self.root.config(cursor="wait")
        self.root.update()

    def display_answer(self, answer, full_response=None):
        self.answer_entry.delete("1.0", tk.END)
        if full_response:
            # 如果需要顯示完整的回應，可以取消下面的註釋
            # formatted_response = json.dumps(full_response, indent=4)
            # self.answer_entry.insert(tk.END, formatted_response)
            pass  # 目前只顯示回答
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
            # 可選：不顯示成功訊息，以避免干擾用戶體驗
            # messagebox.showinfo("Success", "Question and answer saved successfully.")
            self.load_data()  # 刷新數據顯示
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save question and answer: {e}")
            print(f"Database Error: {e}")
            logging.error(f"Database Error: {e}")

    def load_data(self):
        try:
            conn = sqlite3.connect(myDATABASE)
            c = conn.cursor()
            c.execute("SELECT * FROM questions ORDER BY ID DESC")
            rows = c.fetchall()
            conn.close()
            
            # 清除現有的樹狀視圖數據
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 插入新的數據
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
                self.model_var.set(model)  # 設置選中的模型
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
        finally:
            conn.close()

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
            # messagebox.showinfo("Success", "Record deleted successfully.")
            self.load_data()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            logging.error(f"Database Error: {e}")
        finally:
            conn.close()

    def search_data(self):
        topic = self.topic_entry.get().strip()
        if not topic:
            messagebox.showwarning("Input Error", "Please enter a topic to search.")
            return
        
        try:
            conn = sqlite3.connect(myDATABASE)
            c = conn.cursor()
            # 使用 LIKE 進行部分匹配
            c.execute("SELECT * FROM questions WHERE topic LIKE ?", ('%' + topic + '%',))
            rows = c.fetchall()
            conn.close()
            
            # 清除現有數據
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            # 插入搜索結果
            for row in rows:
                self.tree.insert('', tk.END, values=row)
        except Exception as e:
            messagebox.showerror("Database Error", str(e))
            logging.error(f"Database Error: {e}")

    def export_to_text(self):
        try:
            # 打開文件保存對話框，讓用戶選擇保存位置和文件名
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                title="Save as"
            )
            if not file_path:
                return  # 如果用戶取消操作，則退出函數

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
            print(f"Export Error: {e}")
            logging.error(f"Export Error: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    gui = OllamaGUI(root)
    root.mainloop()
