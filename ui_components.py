import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import os
from scp import SCPClient
from server_handler import ServerHandler
import time
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class FileUploaderApp:
    def __init__(self, master):
        self.master = master
        master.withdraw()  # Hide the main window initially
        master.title("文件上傳工具")
        master.geometry("1000x600")

        # Server configuration
        self.server_handler = ServerHandler()

        self.local_path = "./"
        self.local_folder_list = []
        self.last_selected_index = None  # 用於 Shift 多選功能
        self.prompt_credentials()
        self.master.wait_window(self.master.winfo_children()[-1])  # Wait for the credentials window to close

        # Show loading animation
        loading_label = tk.Label(self.master, text="正在連接到伺服器...", font=("Arial", 16))
        loading_label.pack(pady=20)
        self.master.update_idletasks()

        if not self.server_handler.try_connect():
            messagebox.showerror("錯誤", "無法連接到伺服器")
            master.quit()
            exit()
        else:
            loading_label.destroy()  # Remove loading animation
            self.master.deiconify()  # Show the main window after credentials input
            self.create_widgets()

    def prompt_credentials(self):
        credentials_window = tk.Toplevel(self.master)
        credentials_window.title("輸入伺服器用戶名和密碼")
        credentials_window.geometry("300x180")

        tk.Label(credentials_window, text="用戶名:").pack(pady=5)
        username_entry = tk.Entry(credentials_window)
        username_entry.pack(pady=5)

        tk.Label(credentials_window, text="密碼:").pack(pady=5)
        password_entry = tk.Entry(credentials_window, show="*")
        password_entry.pack(pady=5)

        def submit_credentials():
            self.server_handler.username = username_entry.get()
            self.server_handler.password = password_entry.get()
            sub_btn.config(text="連接中...")
            sub_btn.config(state='disabled')
            credentials_window.update_idletasks()
            if self.server_handler.try_connect():
                credentials_window.destroy()
            else:
                sub_btn.config(text="提交")
                sub_btn.config(state='normal')
                messagebox.showerror("錯誤", "無法連接到伺服器")

        sub_btn = tk.Button(credentials_window, text="提交", command=submit_credentials)
        sub_btn.pack(pady=20)

    def create_widgets(self):
        self.create_server_frame()
        self.create_local_frame()
        self.create_search_frame()
        self.create_local_listbox()
        self.create_upload_button()
        self.create_progress_bar()
        self.update_server_folders()

    def create_server_frame(self):
        server_frame = tk.Frame(self.master)
        server_frame.pack(pady=5, fill=tk.X)

        tk.Label(server_frame, text="選擇伺服器資料夾:").pack(side=tk.LEFT, padx=5)
        self.server_folder_var = tk.StringVar(self.master)
        self.server_folder_dropdown = ttk.Combobox(server_frame, textvariable=self.server_folder_var)
        self.server_folder_dropdown.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        tk.Button(server_frame, text="刷新", command=self.update_server_folders).pack(side=tk.RIGHT, padx=5)
        tk.Button(server_frame, text="新建資料夾", command=self.create_server_folder).pack(side=tk.RIGHT, padx=5)
        tk.Button(server_frame, text="重新連線", command=self.reconnect_server).pack(side=tk.RIGHT, padx=5)

    def create_local_frame(self):
        local_frame = tk.Frame(self.master)
        local_frame.pack(pady=5, fill=tk.X)

        tk.Label(local_frame, text="選擇本地資料夾:").pack(side=tk.LEFT, padx=5)
        self.local_folder_var = tk.StringVar(self.master)
        self.local_folder_entry = tk.Entry(local_frame, textvariable=self.local_folder_var)
        self.local_folder_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)
        
        tk.Button(local_frame, text="瀏覽", command=self.browse_local_folder).pack(side=tk.RIGHT, padx=5)
        tk.Button(local_frame, text="重新整理", command=self.refresh_local_folder).pack(side=tk.RIGHT, padx=5)

    def create_search_frame(self):
        search_frame = tk.Frame(self.master)
        search_frame.pack(pady=5, fill=tk.X)

        tk.Label(search_frame, text="尋找資料夾").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar(self.master)
        self.search_entry = tk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        tk.Button(search_frame, text="搜尋", command=lambda: self.show_local_relate_folder(self.search_var.get())).pack(side=tk.RIGHT, padx=5)

    def create_local_listbox(self):
        self.local_listbox = tk.Listbox(self.master, selectmode=tk.EXTENDED, width=50, height=15)
        self.local_listbox.pack(pady=10, expand=True, fill=tk.BOTH)
        
        # 綁定點擊事件以支持 Shift 和 Ctrl/Cmd 多選
        self.local_listbox.bind('<Button-1>', self.on_listbox_click)
        self.local_listbox.bind('<<ListboxSelect>>', self.on_local_folder_select)

    def create_upload_button(self):
        tk.Button(self.master, text="上傳", command=self.upload_files).pack(pady=10)

    def create_progress_bar(self):
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.master, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(pady=10, fill=tk.X, padx=20)

    def update_server_folders(self):
        folders = self.server_handler.list_folders()
        if folders:
            self.server_folder_dropdown['values'] = folders

    def create_server_folder(self):
        new_folder_name = simpledialog.askstring("新建資料夾", "請輸入新資料夾名稱:")
        
        if not new_folder_name:
            messagebox.showerror("錯誤", "未輸入資料夾名稱")
            return

        success = self.server_handler.create_folder(new_folder_name)
        
        if success:
            messagebox.showinfo("成功", f"資料夾 '{new_folder_name}' 已建立")
            # Refresh server folders dropdown after creation
            self.update_server_folders()
            self.server_folder_var.set(new_folder_name)  # Optionally select the new folder

    def browse_local_folder(self):
        self.local_path = filedialog.askdirectory()
        if self.local_path:
            self.local_folder_var.set(self.local_path.split("/")[-1])
            # Only list directories (folders) and sort by modification time (newest first)
            self.local_folder_list = sorted([item for item in os.listdir(self.local_path) 
                           if os.path.isdir(os.path.join(self.local_path, item))], 
                          key=lambda x: os.path.getmtime(os.path.join(self.local_path, x)),
                          reverse=True)
            self.update_local_files()

    def refresh_local_folder(self):
        if self.local_path:
            self.local_folder_list = sorted(os.listdir(self.local_path), key=lambda x: os.path.getctime(os.path.join(self.local_path, x)))
            self.update_local_files()

    def reconnect_server(self):
        if self.server_handler.try_connect():
            messagebox.showinfo("成功", "重新連線成功")
            self.update_server_folders()
        else:
            messagebox.showerror("錯誤", "無法重新連線到伺服器")

    def show_local_relate_folder(self, name):
        self.local_folder_list = [folder for folder in os.listdir(self.local_path) if name in folder]
        self.update_local_files()

    def update_local_files(self):
        self.local_listbox.delete(0, tk.END)
        for item in self.local_folder_list:
            self.local_listbox.insert(tk.END, item)

    def on_listbox_click(self, event):
        """處理滑鼠點擊事件以支持 Shift 和 Ctrl/Cmd 多選"""
        index = self.local_listbox.nearest(event.y)
        
        # 檢查是否按住 Shift 鍵（範圍選擇）
        if event.state & 0x0001:  # Shift key
            if self.last_selected_index is not None:
                # 清除當前選擇
                self.local_listbox.selection_clear(0, tk.END)
                # 選擇範圍
                start = min(self.last_selected_index, index)
                end = max(self.last_selected_index, index)
                for i in range(start, end + 1):
                    self.local_listbox.selection_set(i)
            else:
                self.local_listbox.selection_set(index)
                self.last_selected_index = index
            return "break"
        
        # 檢查是否按住 Ctrl/Cmd 鍵（多選）
        elif event.state & 0x0004 or event.state & 0x0008:  # Control or Command key
            if self.local_listbox.selection_includes(index):
                self.local_listbox.selection_clear(index)
            else:
                self.local_listbox.selection_set(index)
            self.last_selected_index = index
            return "break"
        
        # 一般點擊（單選）
        else:
            self.local_listbox.selection_clear(0, tk.END)
            self.local_listbox.selection_set(index)
            self.last_selected_index = index

    def on_local_folder_select(self, event):
        selected_indices = self.local_listbox.curselection()
        if len(selected_indices) == 1:
            selected_folder = self.local_listbox.get(selected_indices[0])
            folder_path = os.path.join(self.local_path, selected_folder)
            if os.path.isdir(folder_path):
                file_count = len(os.listdir(folder_path))
                # 不使用 messagebox，改為在狀態列顯示（可選）
                # messagebox.showinfo("資料夾內容", f"資料夾 '{selected_folder}' 中有 {file_count} 個檔案")

    def upload_files(self):
        selected_server_folder = self.server_folder_var.get()
        selected_items = [self.local_listbox.get(i) for i in self.local_listbox.curselection()]

        if not selected_server_folder:
            messagebox.showerror("錯誤", "請選擇一個伺服器資料夾")
            return

        if not selected_items:
            messagebox.showerror("錯誤", "請選擇要上傳的文件或資料夾")
            return

        success = self.server_handler.ensure_folder_exists(selected_server_folder)
        if not success:
            messagebox.showerror("錯誤", f"無法建立或確認資料夾 '{selected_server_folder}' 是否存在")
            return

        try:
            with self.server_handler.connect() as ssh:
                with SCPClient(ssh.get_transport(), progress=self.update_progress) as scp:
                    total_items = len(selected_items)
                    for index, item in enumerate(selected_items):
                        local_path = os.path.join(self.local_path, item)
                        
                        # Check if file exists on server
                        stdin, stdout, stderr = ssh.exec_command(f'test -e {self.server_handler.base_path}/{selected_server_folder}/{item} && echo "exists"')
                        file_exists = stdout.read().decode().strip() == "exists"
                        
                        if file_exists:
                            # If file exists, add 'copy' to the name
                            remote_name = item
                            if os.path.isfile(local_path):
                                # For files, insert 'copy' before extension
                                name, ext = os.path.splitext(item)
                                remote_name = f"{name}_copy{ext}"
                            else:  # For directories
                                remote_name = f"{item}_copy"
                                
                            remote_path = f"{self.server_handler.base_path}/{selected_server_folder}/{remote_name}"
                            messagebox.showinfo("檔案已存在", f"'{item}' 已存在於伺服器，將上傳為 '{remote_name}'")
                        else:
                            # Normal path if file doesn't exist
                            remote_path = f"{self.server_handler.base_path}/{selected_server_folder}/{item}"
                        
                        # Upload the file
                        if os.path.isfile(local_path):
                            scp.put(local_path, remote_path)
                        elif os.path.isdir(local_path):
                            print(local_path)
                            scp.put(local_path, remote_path, recursive=True)

                        # Update progress bar
                        progress_percent = (index + 1) / total_items * 100
                        self.progress_var.set(progress_percent)
                        self.master.update_idletasks()

            messagebox.showinfo("成功", "文件上傳完成")
            self.mark_uploaded_items(selected_items)

            # Reset progress bar after upload completion
            self.progress_var.set(0)

        except Exception as e:
            messagebox.showerror("錯誤", f"上傳過程中發生錯誤: {str(e)}")

    def update_progress(self, filename, size, sent):
        percent = float(sent) / float(size) * 100
        self.progress_var.set(percent)
        self.master.update_idletasks()

    def mark_uploaded_items(self, uploaded_items):
        for i in range(self.local_listbox.size()):
            if self.local_listbox.get(i) in uploaded_items:
                self.local_listbox.itemconfig(i, {'bg': 'light green'})
        
        # Clear selection after marking items as uploaded
        self.local_listbox.selection_clear(0, tk.END)