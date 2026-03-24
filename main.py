import tkinter as tk
from src.ui import FileUploaderApp


def main():
    root = tk.Tk()
    app = FileUploaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
