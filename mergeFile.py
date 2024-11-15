import ffmpeg
import os
# 将UTC时间转换为东八区时间
from datetime import datetime, timedelta
from dateutil import parser
import pytz




# 获取当前目录下所有以cut开头的mp4文件
cut_files = [f for f in os.listdir('.') if f.startswith('cut') and f.endswith('.mp4')]

# 按文件名排序
cut_files.sort()

if len(cut_files) == 0:
    print("没有找到需要合并的视频文件")
    exit()

print("将要合并以下文件:")
for f in cut_files:
    print(f)

# 创建一个临时文件来存储文件列表
with open('file_list.txt', 'w', encoding='utf-8') as f:
    for video in cut_files:
        f.write(f"file '{video}'\n")

# 使用ffmpeg合并视频
output_file = 'merged_output.mp4'
try:
    os.system(f'ffmpeg -f concat -safe 0 -i file_list.txt -c copy {output_file}')
    print(f"\n视频合并完成,输出文件: {output_file}")
except Exception as e:
    print(f"合并视频时出错: {str(e)}")
finally:
    # 删除临时文件
    if os.path.exists('file_list.txt'):
        os.remove('file_list.txt')
