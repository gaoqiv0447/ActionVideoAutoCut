import ffmpeg
import os
# 将UTC时间转换为东八区时间
from datetime import datetime, timedelta
from dateutil import parser
import pytz
# from read_timestamp_file import read_timestamps
from read_timestamp import read_timestamps2


video_path = "./DJI_20241115132915_0013_D.MP4"



# 判断单时间点，是否在时间段范围内
def is_within_time_range(time_point, start_time, end_time):
    return start_time <= time_point <= end_time

#一个时间点，转化为两个时间点，前10s后5s
def time_point_to_start_end(time_point, start_time):
    return (time_point - start_time).total_seconds() - 10, (time_point - start_time).total_seconds() + 5


#处理时间戳统一为东八区
def handle_time_stamp(time_stamp):
    utc_time = parser.parse(time_stamp)
    utc_time = utc_time.replace(tzinfo=pytz.UTC)
    tz_cn = pytz.timezone('Asia/Shanghai')
    cn_time = utc_time.astimezone(tz_cn)
    return cn_time

#把绝对时间转换为视频文件的相对时间
def absolute_time_to_video_time(absolute_time, video_start_time):
    return absolute_time - video_start_time


def cut_video(input_path, output_path, start_time, end_time):
    """
    使用ffmpeg切割视频
    :param input_path: 输入视频路径
    :param output_path: 输出视频路径
    :param start_time: 开始时间（秒）
    :param end_time: 结束时间（秒）
    """
    try:
        stream = ffmpeg.input(input_path, ss=start_time, t=end_time-start_time)
        stream = ffmpeg.output(stream, output_path, c='copy')
        ffmpeg.run(stream)
        print(f"视频切割成功：{output_path}")
    except ffmpeg.Error as e:
        print(f"视频切割失败：{str(e)}")

# 获取视频的开始和结束时间
def get_video_start_end_time(video_path):
    # 使用ffmpeg获取视频信息
    probe = ffmpeg.probe(video_path)
    video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')

    # 获取视频创建时间
    creation_time = video_info.get('tags', {}).get('creation_time')

    # 获取视频时长(秒)
    duration = float(probe['format']['duration'])

    # 解析创建时间字符串为datetime对象
    start_time = parser.parse(creation_time)
    # 计算结束时间
    end_time = start_time + timedelta(seconds=duration)

    # 确保时区为UTC
    start_time = start_time.replace(tzinfo=pytz.UTC)
    end_time = end_time.replace(tzinfo=pytz.UTC)

    # 转换为东八区时间
    tz_cn = pytz.timezone('Asia/Shanghai')
    start_time = start_time.astimezone(tz_cn)
    end_time = end_time.astimezone(tz_cn)

    return start_time, end_time

# start_time, end_time = get_video_start_end_time(video_path)
# print(start_time, end_time)

# 读取时间戳列表
timestamp_list = read_timestamps2('time.txt')

# 获取视频的开始和结束时间
start_time, end_time = get_video_start_end_time(video_path)

print("视频开始时间:", start_time)
print("视频结束时间:", end_time)
print("\n在视频时间范围内的时间戳:")

# 遍历时间戳列表,检查哪些在视频时间范围内
for timestamp in timestamp_list:
    # 处理时间戳为东八区时间
    # 判断是否在视频时间范围内
    # 将输入时间戳转换为datetime对象
    ts = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S")
    # 设置时区为东八区
    tz_cn = pytz.timezone('Asia/Shanghai')
    ts = tz_cn.localize(ts)

    if is_within_time_range(ts, start_time, end_time):
        print(f"匹配到时间戳: {ts}")
        start, end = time_point_to_start_end(ts, start_time)
        print(f"开始时间: {start}, 结束时间: {end}")
        output_filename = f"cut_{ts.strftime('%Y%m%d_%H%M%S')}.mp4"
        output_path = os.path.join(os.path.dirname(video_path), output_filename)

        # 调用切割函数
        cut_video(video_path, output_path, start, end)

#---------------------------------------------------------------------


