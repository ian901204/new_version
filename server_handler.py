import paramiko
from paramiko import SSHClient
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class ServerHandler:
    def __init__(self, hostname=None, username=None, password=None, base_path=None, key_path=None):
        # 優先使用傳入的參數，否則從環境變數讀取
        self.hostname = hostname or os.getenv('SERVER_HOSTNAME', '')
        self.username = username or os.getenv('SERVER_USERNAME', '')
        self.password = password or os.getenv('SERVER_PASSWORD', '')
        self.base_path = base_path or os.getenv('SERVER_BASE_PATH', '/home/berxel/ftp')
        self.key_path = key_path or os.getenv('SERVER_KEY_PATH', '')  # SSH 私鑰路徑
        self.key_passphrase = os.getenv('SERVER_KEY_PASSPHRASE', None)  # 私鑰密碼（如果有的話）

    def connect(self):
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # 如果有提供私鑰路徑，使用金鑰認證
        if self.key_path and os.path.exists(self.key_path):
            try:
                # 嘗試載入私鑰
                private_key = paramiko.RSAKey.from_private_key_file(self.key_path, password=self.key_passphrase)
                ssh.connect(self.hostname, username=self.username, pkey=private_key)
            except paramiko.ssh_exception.SSHException:
                # 如果 RSA 失敗，嘗試 Ed25519
                try:
                    private_key = paramiko.Ed25519Key.from_private_key_file(self.key_path, password=self.key_passphrase)
                    ssh.connect(self.hostname, username=self.username, pkey=private_key)
                except:
                    # 最後嘗試 ECDSA
                    private_key = paramiko.ECDSAKey.from_private_key_file(self.key_path, password=self.key_passphrase)
                    ssh.connect(self.hostname, username=self.username, pkey=private_key)
        else:
            # 使用密碼認證（向後兼容）
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