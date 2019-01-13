#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import tempfile
import subprocess, multiprocessing

from crf import encode_crf_segment

def do_clean(segment_list):
    for seg_video in segment_list:
        os.remove(seg_video)

def do_merge(segment_list, output_video):
    with tempfile.NamedTemporaryFile(mode="w+t") as f:
        for seg_video in segment_list:
            f.write("file '%s'\n" % seg_video)
        f.seek(0)
        print(f.read())
        ffmpeg_cmd = 'ffmpeg -hide_banner -f concat -safe 0 -i {segment_list_file} -c copy {output_video} -y'.format(
                segment_list_file=f.name,
                output_video=output_video,
            )
        print(ffmpeg_cmd)
        subprocess.call(ffmpeg_cmd, shell=True)

def encode_crf_segment_unpack(args):
    return encode_crf_segment(*args)

def encode_final(input_video, output_video, v_profile, v_level, v_resolution, seg_start_list, seg_duration_list, ffmpeg_common_settings, seg_crf_list, need_deinterlacing, complex_me, gop, max_thread):
    assert len(seg_duration_list) == len(seg_start_list), "Length of seg_duration_list and seg_start_list are not equal."
    assert len(seg_crf_list) == len(seg_start_list), "Length of seg_crf_list and seg_start_list are not equal."

    seg_size = len(seg_start_list)
    temp_dir = tempfile.mkdtemp()
    seg_format = temp_dir + "/seg_%d.mp4"

    segment_list = []

    arg_list = []
    for seg_idx in range(seg_size):
        start_time = seg_start_list[seg_idx]
        end_time = start_time + seg_duration_list[seg_idx]
        seg_name = seg_format % seg_idx
        cur_arg = [input_video, seg_name, v_profile, v_level, v_resolution, start_time, end_time, ffmpeg_common_settings, seg_crf_list[seg_idx], need_deinterlacing, complex_me, gop]

        arg_list.append(cur_arg)
        segment_list.append(seg_name)
        
    pool = multiprocessing.Pool(processes=max_thread)
    pool.map(encode_crf_segment_unpack, arg_list)
    pool.close()
    pool.join()
    do_merge(segment_list, output_video)
    do_clean(segment_list)
    os.removedirs(temp_dir)

if __name__ == '__main__':
    print("A package that dynmaically encodes videos using variable ffmpeg params")

