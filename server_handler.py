import paramiko
from paramiko import SSHClient
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class ServerHandler:
    def __init__(self, hostname=None, username=None, password=None, base_path=None):
        # 優先使用傳入的參數，否則從環境變數讀取
        self.hostname = hostname or os.getenv('SERVER_HOSTNAME', '')
        self.username = username or os.getenv('SERVER_USERNAME', '')
        self.password = password or os.getenv('SERVER_PASSWORD', '')
        self.base_path = base_path or os.getenv('SERVER_BASE_PATH', '/home/berxel/ftp')

    def connect(self):
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(self.hostname, username=self.username, password=self.password)
        return ssh

    def try_connect(self):
        try:
            with self.connect():
                return True
        except Exception as e:
            print(f"Error connecting to server: {str(e)}")
            return False

    def list_folders(self):
        try:
            with self.connect() as ssh:
                stdin, stdout, stderr = ssh.exec_command(f'ls -d {self.base_path}/*/')
                return [line.strip().split('/')[-2] for line in stdout]
        except Exception as e:
            print(f"Error listing folders: {str(e)}")
            return []

    def create_folder(self, folder_name):
        return self._execute_command(f'mkdir -p {self.base_path}/{folder_name}', "Error creating folder")

    def ensure_folder_exists(self, folder_name):
        command = f'ls {self.base_path}/{folder_name} || mkdir -p {self.base_path}/{folder_name}'
        return self._execute_command(command, "Error ensuring folder exists")

    def _execute_command(self, command, error_message):
        try:
            with self.connect() as ssh:
                ssh.exec_command(command)
            return True
        except Exception as e:
            print(f"{error_message}: {str(e)}")
            return False