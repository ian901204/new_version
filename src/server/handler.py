import paramiko
from paramiko import SSHClient
import os


class ServerHandler:
    """Handles SSH/SFTP server connections and file operations."""

    def __init__(self, hostname=None, username=None, password=None, base_path=None, key_path=None):
        self.hostname = hostname or os.getenv('SERVER_HOSTNAME', '')
        self.username = username or os.getenv('SERVER_USERNAME', '')
        self.password = password or os.getenv('SERVER_PASSWORD', '')
        self.base_path = base_path or os.getenv('SERVER_BASE_PATH', '/home/berxel/ftp')
        self.key_path = key_path or os.getenv('SERVER_KEY_PATH', '')
        self.key_passphrase = os.getenv('SERVER_KEY_PASSPHRASE', None)

    def connect(self):
        ssh = SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if self.key_path and os.path.exists(self.key_path):
            private_key = self._load_private_key()
            if private_key is None:
                raise Exception("無法載入私鑰檔案")
            ssh.connect(self.hostname, username=self.username, pkey=private_key)
        else:
            ssh.connect(self.hostname, username=self.username, password=self.password)

        return ssh

    def _load_private_key(self):
        """Try loading the private key with different formats."""
        key_types = [
            ('Ed25519', paramiko.Ed25519Key),
            ('RSA', paramiko.RSAKey),
            ('ECDSA', paramiko.ECDSAKey),
            ('DSS', paramiko.DSSKey),
        ]

        for key_name, key_class in key_types:
            try:
                return key_class.from_private_key_file(
                    self.key_path,
                    password=self.key_passphrase
                )
            except Exception:
                continue

        return None

    def try_connect(self):
        try:
            ssh = self.connect()
            ssh.close()
            return True, None
        except Exception as e:
            return False, str(e)

    def list_folders(self):
        try:
            with self.connect() as ssh:
                stdin, stdout, stderr = ssh.exec_command(f'ls -d {self.base_path}/*/')
                return [line.strip().split('/')[-2] for line in stdout]
        except Exception as e:
            print(f"Error listing folders: {str(e)}")
            return []

    def create_folder(self, folder_name):
        return self._execute_command(f'mkdir -p {self.base_path}/{folder_name}')

    def ensure_folder_exists(self, folder_name):
        command = f'ls {self.base_path}/{folder_name} || mkdir -p {self.base_path}/{folder_name}'
        return self._execute_command(command)

    def _execute_command(self, command):
        try:
            with self.connect() as ssh:
                ssh.exec_command(command)
            return True
        except Exception as e:
            print(f"Command failed: {str(e)}")
            return False
