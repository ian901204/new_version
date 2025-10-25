import tkinter as tk
from ui_components import FileUploaderApp

def main():
    root = tk.Tk()
    app = FileUploaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()