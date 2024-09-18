import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class PointCloudGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("点云可视化工具")
        self.folder_path = ""
        self.csv_files = []
        self.current_z = None

        self.create_widgets()

    def create_widgets(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        select_button = tk.Button(top_frame, text="选择文件夹", command=self.select_folder)
        select_button.pack(side=tk.LEFT)

        self.folder_label = tk.Label(top_frame, text="未选择文件夹")
        self.folder_label.pack(side=tk.LEFT, padx=10)

        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        list_frame = tk.Frame(main_frame)
        list_frame.pack(side=tk.LEFT, fill=tk.Y)

        list_label = tk.Label(list_frame, text="CSV 文件列表")
        list_label.pack()

        self.listbox = tk.Listbox(list_frame, width=40)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)

        scrollbar = tk.Scrollbar(list_frame, orient="vertical")
        scrollbar.config(command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.bind('<<ListboxSelect>>', self.on_select)

        plot_frame = tk.Frame(main_frame)
        plot_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.fig, (self.ax_xz, self.ax_yz) = plt.subplots(1, 2, figsize=(10, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        bottom_frame = tk.Frame(self.root)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        z_label = tk.Label(bottom_frame, text="输入Z值:")
        z_label.pack(side=tk.LEFT)

        self.z_entry = tk.Entry(bottom_frame)
        self.z_entry.pack(side=tk.LEFT, padx=5)

        confirm_button = tk.Button(bottom_frame, text="确定", command=self.confirm_z)
        confirm_button.pack(side=tk.LEFT, padx=5)

        save_button = tk.Button(bottom_frame, text="保存", command=self.save_file)
        save_button.pack(side=tk.LEFT, padx=5)

    def select_folder(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.folder_path = folder_selected
            self.folder_label.config(text=self.folder_path)
            self.load_csv_files()

    def load_csv_files(self):
        self.csv_files = []
        for root_dir, dirs, files in os.walk(self.folder_path):
            for file in files:
                if file.lower().endswith('.csv'):
                    full_path = os.path.join(root_dir, file)
                    self.csv_files.append(full_path)
        self.update_listbox()

    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        for idx, file in enumerate(self.csv_files, 1):
            display_name = f"{idx}. {os.path.relpath(file, self.folder_path)}"
            self.listbox.insert(tk.END, display_name)
        messagebox.showinfo("加载完成", f"共找到 {len(self.csv_files)} 个CSV文件。")

    def on_select(self, event):
        if not self.listbox.curselection():
            return
        index = self.listbox.curselection()[0]
        file_path = self.csv_files[index]
        self.load_and_plot(file_path)

    def load_and_plot(self, file_path):
        try:
            df = pd.read_csv(file_path,sep=',')
            df.columns = ['X', 'Y', 'Z']

            self.current_data = df
            self.current_file = file_path
            self.plot_projections(df)
        except Exception as e:
            messagebox.showerror("错误", f"无法读取文件 {file_path}。\n{e}")

    def plot_projections(self, df):
        self.ax_xz.clear()
        self.ax_yz.clear()

        self.ax_xz.scatter(df['X'], df['Z'], s=1)
        self.ax_xz.set_xlabel('X')
        self.ax_xz.set_ylabel('Z')
        self.ax_xz.set_title('XZ')
        self.ax_xz.grid(True)

        self.ax_yz.scatter(df['Y'], df['Z'], s=1, color='green')
        self.ax_yz.set_xlabel('Y')
        self.ax_yz.set_ylabel('Z')
        self.ax_yz.set_title('YZ')
        self.ax_yz.grid(True)

        if self.current_z is not None:
            self.ax_xz.axhline(y=self.current_z, color='red', linestyle='--')
            self.ax_yz.axhline(y=self.current_z, color='red', linestyle='--')

        self.fig.tight_layout()
        self.canvas.draw()

    def confirm_z(self):
        z_value = self.z_entry.get()
        try:
            z = float(z_value)
            self.current_z = z
            self.plot_projections(self.current_data)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字。")

    def save_file(self):
        if not hasattr(self, 'current_data') or not hasattr(self, 'current_file'):
            messagebox.showerror("错误", "没有选择任何文件。")
            return
        if self.current_z is None:
            messagebox.showerror("错误", "没有输入Z值。")
            return
        try:
            # 保存原数据和Z线信息
            save_path = self.get_save_path(self.current_file)
            self.current_data.to_csv(save_path, index=False)
            # 另外保存Z值，可以根据需要调整
            with open(save_path, 'a') as f:
                f.write(f"\n# Crown Z value: {self.current_z}\n")
            messagebox.showinfo("成功", f"文件已保存为 {save_path}")
        except Exception as e:
            messagebox.showerror("错误", f"保存文件失败。\n{e}")

    def get_save_path(self, original_path):
        directory, filename = os.path.split(original_path)
        name, ext = os.path.splitext(filename)
        new_filename = f"{name}_crown{ext}"
        return os.path.join(directory, new_filename)

if __name__ == "__main__":
    root = tk.Tk()
    app = PointCloudGUI(root)
    root.mainloop()
