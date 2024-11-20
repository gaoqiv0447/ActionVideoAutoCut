import ffmpeg
import os
from datetime import datetime, timedelta
from dateutil import parser
import pytz
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

class VideoCutterUI:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("视频裁剪工具")
        self.window.geometry("800x600")

        self.video_path = None
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

    def select_video(self):
        filetypes = [("视频文件", "*.mp4;*.MP4")]
        self.video_path = filedialog.askopenfilename(filetypes=filetypes)
        if self.video_path:
            self.video_label.config(text=f"已选择视频: {os.path.basename(self.video_path)}")
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
        if self.video_path and self.timestamp_path and self.output_dir:
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

            # 获取视频的开始和结束时间
            start_time, end_time = get_video_start_end_time(self.video_path)

            self.status_label.config(text=f"视频开始时间: {start_time}\n视频结束时间: {end_time}")

            # 重置进度条
            self.progress_bar["value"] = 0
            total_timestamps = len(timestamp_list)
            processed_count = 0

            # 遍历时间戳列表, 检查哪些在视频时间范围内
            for ts in timestamp_list:
                tz_cn = pytz.timezone('Asia/Shanghai')
                ts = tz_cn.localize(ts)

                if is_within_time_range(ts, start_time, end_time):
                    start, end = time_point_to_start_end(ts, start_time)
                    output_filename = f"cut_{ts.strftime('%Y%m%d_%H%M%S')}.mp4"
                    output_path = os.path.join(self.output_dir, output_filename)

                    # 调用切割函数
                    cut_video(self.video_path, output_path, start, end)

                # 更新进度
                processed_count += 1
                progress = (processed_count / total_timestamps) * 100
                self.progress_bar["value"] = progress
                self.progress_label.config(text=f"处理进度: {processed_count}/{total_timestamps}")
                self.window.update()

            messagebox.showinfo("完成", "视频裁剪完成!")
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
