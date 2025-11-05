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
        self.filtered_folder_list = []  # 用於分頁顯示的資料夾列表
        self.last_selected_index = None  # 用於 Shift 多選功能
        
        # 分頁相關變數
        self.page_size = 50  # 每頁顯示的資料夾數量
        self.current_page = 0
        self.total_pages = 0
        
        self.prompt_credentials()
        self.master.wait_window(self.master.winfo_children()[-1])  # Wait for the credentials window to close

        # Show loading animation
        loading_label = tk.Label(self.master, text="正在連接到伺服器...", font=("Arial", 16))
        loading_label.pack(pady=20)
        self.master.update_idletasks()

        if not self.server_handler.try_connect()[0]:
            messagebox.showerror("錯誤", "無法連接到伺服器")
            master.quit()
            exit()
        else:
            loading_label.destroy()  # Remove loading animation
            self.master.deiconify()  # Show the main window after credentials input
            self.create_widgets()

    def prompt_credentials(self):
        credentials_window = tk.Toplevel(self.master)
        credentials_window.title("輸入伺服器登入資訊")
        credentials_window.geometry("450x320")

        tk.Label(credentials_window, text="用戶名:").pack(pady=5)
        username_entry = tk.Entry(credentials_window, width=40)
        username_entry.pack(pady=5)

        # 認證方式選擇
        auth_method_var = tk.StringVar(value="password")
        
        tk.Label(credentials_window, text="認證方式:").pack(pady=5)
        auth_frame = tk.Frame(credentials_window)
        auth_frame.pack(pady=5)
        
        tk.Radiobutton(auth_frame, text="密碼", variable=auth_method_var, 
                      value="password", command=lambda: toggle_auth_fields()).pack(side=tk.LEFT, padx=10)
        tk.Radiobutton(auth_frame, text="SSH 金鑰", variable=auth_method_var, 
                      value="key", command=lambda: toggle_auth_fields()).pack(side=tk.LEFT, padx=10)

        # 密碼欄位
        password_frame = tk.Frame(credentials_window)
        password_frame.pack(pady=5)
        tk.Label(password_frame, text="密碼:").pack()
        password_entry = tk.Entry(password_frame, show="*", width=40)
        password_entry.pack()

        # SSH 金鑰欄位
        key_frame = tk.Frame(credentials_window)
        tk.Label(key_frame, text="私鑰檔案:").pack()
        key_path_frame = tk.Frame(key_frame)
        key_path_frame.pack()
        key_path_var = tk.StringVar()
        key_path_entry = tk.Entry(key_path_frame, textvariable=key_path_var, width=30)
        key_path_entry.pack(side=tk.LEFT, padx=5)
        
        def browse_key_file():
            key_file = filedialog.askopenfilename(
                title="選擇 SSH 私鑰檔案（不是 .pub 公鑰檔案）",
                initialdir=os.path.expanduser("~/.ssh"),
                filetypes=[("SSH 私鑰", "id_*"), ("PEM 檔案", "*.pem"), ("所有檔案", "*")]
            )
            if key_file:
                # 檢查是否誤選了公鑰檔案
                if key_file.endswith('.pub'):
                    messagebox.showwarning(
                        "警告", 
                        "您選擇的是公鑰檔案（.pub）\n\n"
                        "請選擇私鑰檔案（沒有 .pub 副檔名）\n"
                        f"例如：{key_file[:-4]}"
                    )
                    return
                key_path_var.set(key_file)
        
        tk.Button(key_path_frame, text="瀏覽", command=browse_key_file).pack(side=tk.LEFT)
        
        tk.Label(key_frame, text="私鑰密碼 (選填):").pack(pady=(10, 0))
        key_passphrase_entry = tk.Entry(key_frame, show="*", width=40)
        key_passphrase_entry.pack()

        def toggle_auth_fields():
            if auth_method_var.get() == "password":
                password_frame.pack(pady=5)
                key_frame.pack_forget()
            else:
                password_frame.pack_forget()
                key_frame.pack(pady=5)

        toggle_auth_fields()

        def submit_credentials():
            self.server_handler.username = username_entry.get()
            
            if auth_method_var.get() == "password":
                self.server_handler.password = password_entry.get()
                self.server_handler.key_path = ""
            else:
                self.server_handler.key_path = key_path_var.get()
                self.server_handler.key_passphrase = key_passphrase_entry.get() if key_passphrase_entry.get() else None
                self.server_handler.password = ""
            
            if not self.server_handler.username:
                messagebox.showerror("錯誤", "請輸入用戶名")
                return
            
            if auth_method_var.get() == "key" and not self.server_handler.key_path:
                messagebox.showerror("錯誤", "請選擇 SSH 私鑰檔案")
                return
            
            # 再次確認不是公鑰檔案
            if auth_method_var.get() == "key" and self.server_handler.key_path.endswith('.pub'):
                messagebox.showerror(
                    "錯誤", 
                    "您選擇的是公鑰檔案（.pub）\n\n"
                    "請選擇私鑰檔案（沒有 .pub 副檔名）"
                )
                return
            
            sub_btn.config(text="連接中...")
            sub_btn.config(state='disabled')
            credentials_window.update_idletasks()
            
            success, error_detail = self.server_handler.try_connect()
            if success:
                credentials_window.destroy()
            else:
                sub_btn.config(text="提交")
                sub_btn.config(state='normal')
                error_msg = "無法連接到伺服器\n\n"
                if auth_method_var.get() == "key":
                    error_msg += "可能的原因:\n"
                    error_msg += "• SSH 私鑰檔案格式不正確或損壞\n"
                    error_msg += "• 私鑰密碼錯誤（如有設定）\n"
                    error_msg += "• 伺服器不允許此金鑰登入\n"
                    error_msg += "• 伺服器連線資訊錯誤\n\n"
                else:
                    error_msg += "請確認用戶名和密碼是否正確\n\n"
                
                if error_detail:
                    error_msg += f"詳細錯誤:\n{error_detail}"
                
                messagebox.showerror("連線錯誤", error_msg)

        sub_btn = tk.Button(credentials_window, text="提交", command=submit_credentials)
        sub_btn.pack(pady=20)

    def create_widgets(self):
        self.create_server_frame()
        self.create_local_frame()
        self.create_search_frame()
        self.create_pagination_frame()
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

    def create_pagination_frame(self):
        """創建分頁控制框架"""
        pagination_frame = tk.Frame(self.master)
        pagination_frame.pack(pady=5, fill=tk.X)

        self.page_info_label = tk.Label(pagination_frame, text="頁數: 0 / 0 (總共 0 個資料夾)")
        self.page_info_label.pack(side=tk.LEFT, padx=10)

        tk.Button(pagination_frame, text="◀◀ 首頁", command=self.go_to_first_page).pack(side=tk.LEFT, padx=2)
        tk.Button(pagination_frame, text="◀ 上一頁", command=self.go_to_prev_page).pack(side=tk.LEFT, padx=2)
        tk.Button(pagination_frame, text="下一頁 ▶", command=self.go_to_next_page).pack(side=tk.LEFT, padx=2)
        tk.Button(pagination_frame, text="末頁 ▶▶", command=self.go_to_last_page).pack(side=tk.LEFT, padx=2)
        
        # 每頁顯示數量設置
        tk.Label(pagination_frame, text="每頁顯示:").pack(side=tk.LEFT, padx=(20, 5))
        self.page_size_var = tk.StringVar(value="50")
        page_size_combo = ttk.Combobox(pagination_frame, textvariable=self.page_size_var, 
                                       values=["20", "50", "100", "200"], width=8)
        page_size_combo.pack(side=tk.LEFT, padx=2)
        page_size_combo.bind('<<ComboboxSelected>>', self.on_page_size_change)

    def create_local_listbox(self):
        self.local_listbox = tk.Listbox(self.master, selectmode=tk.EXTENDED, width=50, height=15)
        self.local_listbox.pack(pady=10, expand=True, fill=tk.BOTH)
        
        # 綁定點擊事件以支持 Shift 和 Ctrl/Cmd 多選
        self.local_listbox.bind('<Button-1>', self.on_listbox_click)
        # 移除 ListboxSelect 事件綁定以避免彈窗

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

    def sort_folders_by_creation_time(self, folder_list):
        """統一的排序方法：按建立時間排序（最新的在前）"""
        try:
            return sorted(folder_list, 
                         key=lambda x: os.path.getctime(os.path.join(self.local_path, x)),
                         reverse=True)
        except Exception as e:
            print(f"排序錯誤: {str(e)}")
            return folder_list

    def calculate_pagination(self):
        """計算分頁信息"""
        total_items = len(self.local_folder_list)
        self.total_pages = (total_items + self.page_size - 1) // self.page_size if total_items > 0 else 0
        if self.current_page >= self.total_pages and self.total_pages > 0:
            self.current_page = self.total_pages - 1
        elif self.current_page < 0:
            self.current_page = 0

    def update_page_info(self):
        """更新分頁資訊顯示"""
        total_items = len(self.local_folder_list)
        current_page_display = self.current_page + 1 if self.total_pages > 0 else 0
        self.page_info_label.config(
            text=f"頁數: {current_page_display} / {self.total_pages} (總共 {total_items} 個資料夾)"
        )

    def get_current_page_items(self):
        """獲取當前頁的資料夾列表"""
        start_idx = self.current_page * self.page_size
        end_idx = start_idx + self.page_size
        return self.local_folder_list[start_idx:end_idx]

    def go_to_first_page(self):
        """跳到首頁"""
        self.current_page = 0
        self.update_local_files()

    def go_to_prev_page(self):
        """上一頁"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_local_files()

    def go_to_next_page(self):
        """下一頁"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_local_files()

    def go_to_last_page(self):
        """跳到末頁"""
        if self.total_pages > 0:
            self.current_page = self.total_pages - 1
            self.update_local_files()

    def on_page_size_change(self, event=None):
        """當每頁顯示數量改變時"""
        try:
            self.page_size = int(self.page_size_var.get())
            self.current_page = 0
            self.update_local_files()
        except ValueError:
            pass

    def browse_local_folder(self):
        self.local_path = filedialog.askdirectory()
        if self.local_path:
            self.local_folder_var.set(self.local_path.split("/")[-1])
            # 只列出資料夾並按建立時間排序（最新的在前）
            folders = [item for item in os.listdir(self.local_path) 
                      if os.path.isdir(os.path.join(self.local_path, item))]
            self.local_folder_list = self.sort_folders_by_creation_time(folders)
            self.current_page = 0  # 重置到第一頁
            self.update_local_files()

    def refresh_local_folder(self):
        if self.local_path:
            folders = [item for item in os.listdir(self.local_path)
                      if os.path.isdir(os.path.join(self.local_path, item))]
            self.local_folder_list = self.sort_folders_by_creation_time(folders)
            self.current_page = 0  # 重置到第一頁
            self.update_local_files()

    def reconnect_server(self):
        success, error_detail = self.server_handler.try_connect()
        if success:
            messagebox.showinfo("成功", "重新連線成功")
            self.update_server_folders()
        else:
            error_msg = "無法重新連線到伺服器"
            if error_detail:
                error_msg += f"\n\n詳細錯誤:\n{error_detail}"
            messagebox.showerror("錯誤", error_msg)

    def show_local_relate_folder(self, name):
        # 先過濾，再按建立時間排序
        folders = [folder for folder in os.listdir(self.local_path) 
                  if name in folder and os.path.isdir(os.path.join(self.local_path, folder))]
        self.local_folder_list = self.sort_folders_by_creation_time(folders)
        self.current_page = 0  # 重置到第一頁
        self.update_local_files()

    def update_local_files(self):
        """更新顯示當前頁的資料夾列表"""
        self.calculate_pagination()
        self.update_page_info()
        
        self.local_listbox.delete(0, tk.END)
        current_page_items = self.get_current_page_items()
        for item in current_page_items:
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
        """更新進度條"""
        if size > 0:
            percent = float(sent) / float(size) * 100
            self.progress_var.set(percent)
            self.master.update_idletasks()

    def mark_uploaded_items(self, uploaded_items):
        for i in range(self.local_listbox.size()):
            if self.local_listbox.get(i) in uploaded_items:
                self.local_listbox.itemconfig(i, {'bg': 'light green'})
        
        # Clear selection after marking items as uploaded
        self.local_listbox.selection_clear(0, tk.END)