import cv2
import numpy as np
import ffmpeg
import subprocess

from glob import glob
import os

from PIL import Image

import pdb


def read_video(input_video_path):
    probe = ffmpeg.probe(input_video_path, v='error', select_streams='v:0', show_entries='stream=width,height,r_frame_rate')
    width = probe['streams'][0]['width']
    height = probe['streams'][0]['height']
    
    process = (
        ffmpeg
        .input(input_video_path)
        .output('pipe:1', format='rawvideo', pix_fmt='rgb24')
        .run_async(pipe_stdout=True)
    )

    video_frames = []
    while True:
        in_bytes = process.stdout.read(width * height * 3)  # 每帧的字节数
        if not in_bytes:
            break
        frame = np.frombuffer(in_bytes, np.uint8).reshape([height, width, 3])  # 转换为numpy数组
        video_frames.append(frame)
    
    process.stdout.close()
    process.wait()

    return video_frames, width, height


def write_video(output_video_path, frames, width, height, fps=30):
    process = (
        ffmpeg
        .input('pipe:0', format='rawvideo', pix_fmt='rgb24', s=f'{width}x{height}', framerate=fps)
        .output(output_video_path, vcodec='libx264', pix_fmt='yuv420p', crf=8)
        .run_async(pipe_stdin=True)
    )

    for frame in frames:
        process.stdin.write(frame.tobytes())  # 将每帧数据写入到ffmpeg的stdin
    
    process.stdin.close()
    process.wait()


if __name__ == "__main__":
    # video_paths = ['idx18293_view0_rank4.mp4', 
    #                'idx69_view0_rank0.mp4', 
    #                'idx1817_view0_rank0.mp4', 
    #                'idx16599_view0_rank4.mp4']
    video_paths = sorted(glob('./src2/*.mp4'))
    # video_paths = ['./weather_1.mp4']
    # output_path = 'output_video.mp4'
    rdir = './reshape2'
    os.makedirs(rdir, exist_ok=True)

    for vpath in video_paths:
        frames, width, height = read_video(vpath)

        for fidx, frame in enumerate(frames):
            # frame = np.concatenate([frame[:, :width // 2], frame[:, width // 2:]], axis=0)
            frames[fidx] = frame
        
        rpath = os.path.join(rdir, os.path.basename(vpath))
        write_video(rpath, frames, frames[0].shape[1], frames[0].shape[0], fps=6)

    
    # frames_all = [[] for _ in range(17)]
    # for vpath in video_paths:
    #     frames, width, height = read_video(vpath)

    #     for fidx, frame in enumerate(frames):
    #         frame = Image.fromarray(frame)
    #         w, h = frame.size
    #         frame = frame.resize((w // 2, h // 2), resample=Image.BICUBIC)
    #         frames_all[fidx].append(np.array(frame))
    
    # for fidx in range(len(frames_all)):
    #     frames_all[fidx] = np.concatenate(frames_all[fidx], axis=0)
    
    # write_video('res.mp4', frames_all, frames_all[0].shape[1], frames_all[0].shape[0], fps=6)
    # concat_videos_vertically(video_paths, output_path)
