import ffmpeg
import os
from datetime import datetime, timedelta
from dateutil import parser
import pytz
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import subprocess

class VideoCutterUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("视频裁剪工具")
        self.window.geometry("800x600")

        self.video_paths = []  # 改为列表存储多个视频路径
        self.timestamp_path = None
        self.output_dir = None

        # 选择视频按钮
        self.select_video_btn = tk.Button(
            self.window,
            text="选择视频文件",
            command=self.select_video,
            width=20,
            height=2
        )
        self.select_video_btn.pack(pady=20)

        # 视频路径标签
        self.video_label = tk.Label(self.window, text="未选择视频")
        self.video_label.pack()

        # 选择时间戳文件按钮
        self.select_timestamp_btn = tk.Button(
            self.window,
            text="选择时间戳文件",
            command=self.select_timestamp,
            width=20,
            height=2
        )
        self.select_timestamp_btn.pack(pady=20)

        # 时间戳文件路径标签
        self.timestamp_label = tk.Label(self.window, text="未选择时间戳文件")
        self.timestamp_label.pack()

        # 选择输出目录按钮
        self.select_output_btn = tk.Button(
            self.window,
            text="选择输出目录",
            command=self.select_output_dir,
            width=20,
            height=2
        )
        self.select_output_btn.pack(pady=20)

        # 输出目录标签
        self.output_dir_label = tk.Label(self.window, text="未选择输出目录")
        self.output_dir_label.pack()

        # 开始裁剪按钮
        self.start_btn = tk.Button(
            self.window,
            text="开始裁剪",
            command=self.start_cutting,
            width=20,
            height=2,
            state=tk.DISABLED
        )
        self.start_btn.pack(pady=20)

        # 合并视频按钮
        self.merge_btn = tk.Button(
            self.window,
            text="合并视频",
            command=self.merge_videos,
            width=20,
            height=2
        )
        self.merge_btn.pack(pady=20)

        # 进度条
        self.progress_bar = ttk.Progressbar(
            self.window,
            orient="horizontal",
            length=300,
            mode="determinate"
        )
        self.progress_bar.pack(pady=10)

        # 进度标签
        self.progress_label = tk.Label(self.window, text="")
        self.progress_label.pack()

        # 状态标签
        self.status_label = tk.Label(self.window, text="")
        self.status_label.pack(pady=10)

    def merge_videos(self):
        try:
            # 获取当前目录下及所有子目录下的所有以cut开头的mp4文件
            cut_files = [os.path.join(root, f) for root, _, files in os.walk(self.output_dir) for f in files if f.startswith('cut') and f.endswith('.mp4')]

            if not cut_files:
                messagebox.showinfo("提示", "没有找到需要合并的视频文件")
                return

            # 按文件名排序
            cut_files.sort()

            # 生成输出文件名（当前日期+mergeFile.mp4）
            current_date = datetime.now().strftime('%Y%m%d')
            output_file = os.path.join(self.output_dir, f'{current_date}_mergeFile.mp4')

            # 创建临时文件列表
            list_file = os.path.join(self.output_dir, 'file_list.txt')
            with open(list_file, 'w', encoding='utf-8') as f:
                for video in cut_files:
                    f.write(f"file '{os.path.join(self.output_dir, video)}'\n")

            # 使用ffmpeg合并视频
            merge_command = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', list_file,
                '-c', 'copy',
                output_file
            ]

            subprocess.run(merge_command, check=True)

            # 删除临时文件
            os.remove(list_file)

            messagebox.showinfo("完成", f"视频合并完成!\n输出文件: {output_file}")

        except Exception as e:
            messagebox.showerror("错误", f"合并视频时出错: {str(e)}")

    def select_video(self):
        filetypes = [("视频文件", "*.mp4;*.MP4")]
        self.video_paths = list(filedialog.askopenfilenames(filetypes=filetypes))  # 使用askopenfilenames允许多选
        if self.video_paths:
            # 显示选中的视频数量和名称
            video_names = [os.path.basename(path) for path in self.video_paths]
            self.video_label.config(text=f"已选择{len(self.video_paths)}个视频:\n" + "\n".join(video_names))
            self.check_start_button()

    def select_timestamp(self):
        filetypes = [("文本文件", "*.txt")]
        self.timestamp_path = filedialog.askopenfilename(filetypes=filetypes)
        if self.timestamp_path:
            self.timestamp_label.config(text=f"已选择时间戳文件: {os.path.basename(self.timestamp_path)}")
            self.check_start_button()

    def select_output_dir(self):
        self.output_dir = filedialog.askdirectory()
        if self.output_dir:
            self.output_dir_label.config(text=f"输出目录: {self.output_dir}")
            self.check_start_button()

    def check_start_button(self):
        if self.video_paths and self.timestamp_path and self.output_dir:
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.DISABLED)

    def start_cutting(self):
        try:
            # 读取时间戳列表
            timestamp_list = read_timestamps(self.timestamp_path)
            print(timestamp_list)

            # 处理时间戳列表, 删除相邻时间戳间隔小于10秒的后一个元素
            timestamp_list = handle_time_stamp(timestamp_list)
            print(timestamp_list)

            # 计算总处理数量（视频数量 × 时间戳数量）
            total_tasks = len(self.video_paths) * len(timestamp_list)
            processed_count = 0

            # 重置进度条
            self.progress_bar["value"] = 0

            # 遍历每个视频文件
            for video_path in self.video_paths:
                try:
                    # 获取当前视频的开始和结束时间
                    start_time, end_time = get_video_start_end_time(video_path)
                    video_name = os.path.basename(video_path)
                    self.status_label.config(text=f"正在处理: {video_name}\n开始时间: {start_time}\n结束时间: {end_time}")

                    # 为每个视频创建单独的输出子目录
                    video_output_dir = os.path.join(self.output_dir, os.path.splitext(video_name)[0])
                    os.makedirs(video_output_dir, exist_ok=True)

                    # 遍历时间戳列表, 检查哪些在视频时间范围内
                    for ts in timestamp_list:
                        tz_cn = pytz.timezone('Asia/Shanghai')
                        ts = tz_cn.localize(ts)

                        if is_within_time_range(ts, start_time, end_time):
                            start, end = time_point_to_start_end(ts, start_time)
                            output_filename = f"cut_{ts.strftime('%Y%m%d_%H%M%S')}.mp4"
                            output_path = os.path.join(video_output_dir, output_filename)

                            # 调用切割函数
                            cut_video(video_path, output_path, start, end)

                        # 更新进度
                        processed_count += 1
                        progress = (processed_count / total_tasks) * 100
                        self.progress_bar["value"] = progress
                        self.progress_label.config(text=f"总进度: {processed_count}/{total_tasks}")
                        self.window.update()

                except Exception as e:
                    print(f"处理视频 {video_name} 时出错: {str(e)}")
                    continue

            messagebox.showinfo("完成", "所有视频裁剪完成!")
            self.progress_label.config(text="裁剪完成!")

        except Exception as e:
            messagebox.showerror("错误", f"处理过程中出现错误: {str(e)}")
            self.progress_label.config(text="处理出错!")

    def run(self):
        self.window.mainloop()

# 保持原有的辅助函数不变
def is_within_time_range(time_point, start_time, end_time):
    return start_time <= time_point <= end_time

# 将时间点转换为视频时间
def time_point_to_start_end(time_point, start_time):
    return (time_point - start_time).total_seconds() - 10, (time_point - start_time).total_seconds() + 5

# 将绝对时间转换为视频时间
def absolute_time_to_video_time(absolute_time, video_start_time):
    return absolute_time - video_start_time

# 切割视频
def cut_video(input_path, output_path, start_time, end_time):
    try:
        stream = ffmpeg.input(input_path, ss=start_time, t=end_time-start_time)
        stream = ffmpeg.output(stream, output_path, c='copy')
        ffmpeg.run(stream)
        print(f"视频切割成功：{output_path}")
    except ffmpeg.Error as e:
        print(f"视频切割失败：{str(e)}")

# 获取视频的开始和结束时间
def get_video_start_end_time(video_path):
    probe = ffmpeg.probe(video_path)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    creation_time = video_info.get('tags', {}).get('creation_time')
    duration = float(probe['format']['duration'])
    start_time = parser.parse(creation_time)
    end_time = start_time + timedelta(seconds=duration)
    start_time = start_time.replace(tzinfo=pytz.UTC)
    end_time = end_time.replace(tzinfo=pytz.UTC)
    tz_cn = pytz.timezone('Asia/Shanghai')
    start_time = start_time.astimezone(tz_cn)
    end_time = end_time.astimezone(tz_cn)
    return start_time, end_time

# 读取时间戳文件
def read_timestamps(file_path):
    try:
        timestamps = []
        with open(file_path, 'r') as f:
            content = f.read().strip()
            # 按逗号分割时间戳
            timestamp_list = content.split(',')
            # 解析为 datetime 对象，并过滤空字符串
            timestamps = [
                datetime.strptime(ts.strip(), '%Y-%m-%dT%H:%M:%S')
                for ts in timestamp_list
                if ts.strip()
            ]
        # 使用 set 去重，然后转回 list
        timestamps = list(set(timestamps))
        # 按时间排序
        timestamps.sort()
        print("读取时间戳文件:", timestamps)

        return timestamps
    except Exception as e:
        print(f"读取时间戳文件时发生错误: {str(e)}")
        return []

# 处理时间戳列表,删除相邻时间戳间隔小于10s的后一个元素
def handle_time_stamp(timestamps):
    try:

        # 存储需要删除的时间戳索引
        to_remove = []

        # 检查相邻时间戳
        for i in range(len(timestamps)-1):
            time_diff = (timestamps[i+1] - timestamps[i]).total_seconds()
            if time_diff < 10:
                to_remove.append(i+1)

        # 从后向前删除,避免索引变化
        for index in sorted(to_remove, reverse=True):
            timestamps.pop(index)

        # 打印处理后相邻时间戳的间隔
        print("相邻时间戳间隔(秒):")
        for i in range(len(timestamps)-1):
            time_diff = (timestamps[i+1] - timestamps[i]).total_seconds()
            print(f"{timestamps[i]} -> {timestamps[i+1]}: {time_diff}秒")

        return timestamps
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    app = VideoCutterUI()
    app.run()
