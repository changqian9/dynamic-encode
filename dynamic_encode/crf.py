#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import tempfile
import subprocess, multiprocessing

from tool import do_merge, do_clean

def encode_crf_segment(input_video, output_video, start_time, end_time, level, resolution, video_profile, video_filter, \
    ffmpeg_common_settings, crf, complex_me, gop, tune, color_str):
    x264_other_opt = ':me=umh:merange=32:subme=10'

    start_end_trim = ''
    if start_time >= 0 and end_time > 0:
        start_end_trim = '-ss {START_TIME} -to {END_TIME}'.format( START_TIME=start_time, END_TIME=end_time )

    ffmpeg_vcmd = 'ffmpeg {START_END_TRIM} -i {INPUT_VIDEO} -filter_complex "[0:v]{V_FILTER}scale={RESOLUTION}[vout]" \
            -an -map [vout] {FFMPEG_COMMON_SETTINGS} -level {LEVEL} -profile:v {V_PROFILE} -crf {CRF} -tune {TUNE} \
            -x264opts no-scenecut:keyint={GOP}:min-keyint={GOP}{X264_OTHER_OPT} -pix_fmt yuv420p {COLOR_STR} -f mp4 {OUTPUT_VIDEO} -y'.format(
                INPUT_VIDEO=input_video,
                START_END_TRIM=start_end_trim,
                FFMPEG_COMMON_SETTINGS=ffmpeg_common_settings,
                LEVEL=level,
                V_FILTER=video_filter,
                V_PROFILE=video_profile,
                RESOLUTION=resolution,
                CRF=crf,
                GOP=gop,
                TUNE=tune,
                COLOR_STR=color_str,
                X264_OTHER_OPT=x264_other_opt if complex_me else "",
                OUTPUT_VIDEO=output_video,
            )

    print(ffmpeg_vcmd)
    ret = subprocess.call(ffmpeg_vcmd, shell=True)
    if ret != 0:
        return None
    return output_video

def encode_crf_segment_unpack(args):
    return encode_crf_segment(*args)

def encode_crf_final(input_video, output_video, preroll, seg_start_list, seg_duration_list, level, resolution, video_profile, \
    video_filter, ffmpeg_common_settings, seg_crf_list, complex_me, gop, tune, color_str, non_ad_time_intervals, max_thread):

    assert len(seg_duration_list) == len(seg_start_list), "Length of seg_duration_list and seg_start_list are not equal."
    assert len(seg_crf_list) == len(seg_start_list), "Length of seg_crf_list and seg_start_list are not equal."

    seg_size = len(seg_start_list)
    temp_dir = tempfile.mkdtemp()
    seg_format = temp_dir + '/seg_%d.mp4'

    segment_list = []
    arg_list = []

    final_seg_start_list = []
    final_seg_duration_list = []

    if non_ad_time_intervals is not None and len(non_ad_time_intervals) > 0:
        for interval_idx in range(len(non_ad_time_intervals)):
            non_ad_start_time = non_ad_time_intervals[interval_idx][0]
            non_ad_end_time = non_ad_time_intervals[interval_idx][1]

            for seg_idx in range(len(seg_start_list)):
                seg_start_time = seg_start_list[seg_idx]
                seg_end_time = seg_start_time + seg_duration_list[seg_idx]

                if seg_start_time >= seg_end_time:
                    continue

                if seg_start_time < non_ad_end_time:
                    if seg_start_time >= non_ad_start_time:
                        final_seg_start_list.append(seg_start_time)
                        if seg_end_time <= non_ad_end_time:
                            final_seg_duration_list.append(seg_duration_list[seg_idx])
                            seg_duration_list[seg_idx] = -1.0 # mark as processed
                        else:
                            final_seg_duration_list.append(non_ad_end_time - seg_start_time)
                            seg_duration_list[seg_idx] = -1.0
                            seg_start_list.insert(seg_idx + 1, non_ad_end_time)
                            seg_duration_list.insert(seg_idx + 1, seg_end_time - non_ad_end_time)
                            break
                    elif seg_end_time > non_ad_start_time:
                    # seg_start_time < non_ad_start_time
                        final_seg_start_list.append(non_ad_start_time)
                        if seg_end_time <= non_ad_end_time:
                            final_seg_duration_list.append(seg_end_time - non_ad_start_time)
                            seg_duration_list[seg_idx] = -1.0
                        else:
                            final_seg_duration_list.append(non_ad_end_time - non_ad_start_time)
                            seg_duration_list[seg_idx] = -1.0
                            seg_start_list.insert(seg_idx + 1, non_ad_end_time)
                            seg_duration_list.insert(seg_idx + 1, seg_end_time - non_ad_end_time)
                            break

    else:
        final_seg_start_list = seg_start_list
        final_seg_duration_list = seg_duration_list

    print(final_seg_start_list, final_seg_duration_list)
    seg_size = len(final_seg_start_list)

    if preroll is not None:
        seg_name = seg_format % 0
        cur_arg = [preroll, seg_name, 0, 0, level, resolution, video_profile, video_filter, ffmpeg_common_settings, \
            seg_crf_list[0], complex_me, gop, tune, color_str]

        arg_list.append(cur_arg)
        segment_list.append(seg_name)

    for seg_idx in range(seg_size):
        start_time = final_seg_start_list[seg_idx]
        end_time = start_time + final_seg_duration_list[seg_idx]
        seg_name = seg_format % (seg_idx + 1)
        cur_arg = [input_video, seg_name, start_time, end_time, level, resolution, video_profile, video_filter, \
            ffmpeg_common_settings, seg_crf_list[seg_idx], complex_me, gop, tune, color_str]

        arg_list.append(cur_arg)
        segment_list.append(seg_name)

    pool = multiprocessing.Pool(processes=max_thread)
    pool.map(encode_crf_segment_unpack, arg_list)
    pool.close()
    pool.join()
    do_merge(segment_list, output_video)
    do_clean(segment_list)
    os.removedirs(temp_dir)
