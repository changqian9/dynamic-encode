#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import tempfile
import subprocess, multiprocessing

from tool import do_merge, do_clean

THREAD_TIMEOUT = 8 * 60 * 60 # 8 hour

def encode_crf_segment(input_video, output_video, start_time, end_time, level, resolution, video_profile, video_filter,
    ffmpeg_common_settings, crf, complex_me, gop, tune, color_str):
    x264_other_opt = ':me=umh:merange=32:subme=10'

    start_end_trim = ''
    if start_time >= 0 and end_time > 0:
        start_end_trim = '-ss {START_TIME} -to {END_TIME}'.format( START_TIME=start_time, END_TIME=end_time )

    ffmpeg_vcmd = 'ffmpeg -hide_banner -xerror -v warning -nostdin {START_END_TRIM} -i {INPUT_VIDEO} -filter_complex "[0:v]{V_FILTER}scale={RESOLUTION}[vout]" \
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

    ret = subprocess.call(ffmpeg_vcmd, shell=True)
    return ret, ffmpeg_vcmd

def encode_crf_segment_unpack(args):
    return encode_crf_segment(*args)

def apply_non_ad_intervals(seg_start_list, seg_duration_list, seg_crf_list, non_ad_time_intervals):
    assert len(seg_duration_list) > 0, "Error: segment list empty."

    final_seg_start_list = []
    final_seg_duration_list = []
    final_seg_crf_list = []

    SEGMENT_MIN_IN_SECONDS = 0.25

    # check whether non_ad segments are too short
    for seg_idx in range(len(non_ad_time_intervals)):
        assert non_ad_time_intervals[seg_idx][1] - non_ad_time_intervals[seg_idx][0] >= SEGMENT_MIN_IN_SECONDS * 2, "Error: non ad segment %d [%f , %f] is too short (< %f)" % (seg_idx, non_ad_time_intervals[seg_idx][0], non_ad_time_intervals[seg_idx][1], SEGMENT_MIN_IN_SECONDS * 2)

    # check whether shot segments are consistent. check too small shot segments and merge it if exists
    seg_idx = 0
    while seg_idx < len(seg_duration_list) - 1:
        while seg_idx < len(seg_duration_list) - 1 and seg_duration_list[seg_idx] < SEGMENT_MIN_IN_SECONDS:
            assert seg_start_list[seg_idx] + seg_duration_list[seg_idx] == seg_start_list[seg_idx + 1], "Error: segments are not consistent."
            seg_duration_list[seg_idx + 1] += seg_duration_list[seg_idx]
            seg_start_list[seg_idx + 1] = seg_start_list[seg_idx]
            seg_crf_list[seg_idx + 1] = min(seg_crf_list[seg_idx], seg_crf_list[seg_idx + 1])

            seg_start_list.pop(seg_idx)
            seg_duration_list.pop(seg_idx)
            seg_crf_list.pop(seg_idx)

        seg_idx += 1

    # check whether last shot segment is too short and merge it if exists
    if seg_duration_list[-1] < SEGMENT_MIN_IN_SECONDS:
        assert len(seg_duration_list) > 1, "Error: segment is too short and can not be merged."
        seg_duration_list[-2] += seg_duration_list[-1]
        seg_crf_list[-2] = min(seg_crf_list[-2], seg_crf_list[-1])
        seg_start_list.pop()
        seg_duration_list.pop()
        seg_crf_list.pop()

    if non_ad_time_intervals is not None and len(non_ad_time_intervals) > 0:
        for interval_idx in range(len(non_ad_time_intervals)):
            non_ad_start_time = non_ad_time_intervals[interval_idx][0]
            non_ad_end_time = non_ad_time_intervals[interval_idx][1]

            for seg_idx in range(len(seg_start_list)):
                seg_start_time = seg_start_list[seg_idx]
                seg_end_time = seg_start_time + seg_duration_list[seg_idx]
                seg_crf_value = seg_crf_list[seg_idx]

                if seg_start_time >= seg_end_time:
                    continue

                if seg_start_time < non_ad_end_time:
                    if seg_start_time >= non_ad_start_time:
                        final_seg_start_list.append(seg_start_time)
                        final_seg_crf_list.append(seg_crf_value)

                        if seg_end_time <= non_ad_end_time:
                            final_seg_duration_list.append(seg_duration_list[seg_idx])
                            seg_duration_list[seg_idx] = -1.0 # mark as processed
                        else:
                            final_seg_duration_list.append(non_ad_end_time - seg_start_time)
                            seg_duration_list[seg_idx] = -1.0
                            seg_start_list.insert(seg_idx + 1, non_ad_end_time)
                            seg_duration_list.insert(seg_idx + 1, seg_end_time - non_ad_end_time)
                            seg_crf_list.insert(seg_idx + 1, seg_crf_value)
                            break
                    elif seg_end_time > non_ad_start_time:
                    # seg_start_time < non_ad_start_time
                        final_seg_start_list.append(non_ad_start_time)
                        final_seg_crf_list.append(seg_crf_value)
                        if seg_end_time <= non_ad_end_time:
                            final_seg_duration_list.append(seg_end_time - non_ad_start_time)
                            seg_duration_list[seg_idx] = -1.0
                        else:
                            final_seg_duration_list.append(non_ad_end_time - non_ad_start_time)
                            seg_duration_list[seg_idx] = -1.0
                            seg_start_list.insert(seg_idx + 1, non_ad_end_time)
                            seg_duration_list.insert(seg_idx + 1, seg_end_time - non_ad_end_time)
                            seg_crf_list.insert(seg_idx + 1, seg_crf_value)
                            break

    else:
        final_seg_start_list = seg_start_list
        final_seg_duration_list = seg_duration_list
        final_seg_crf_list = seg_crf_list

    # check too small segments and merge it if exists
    seg_idx = 0
    while seg_idx < len(final_seg_start_list):
        if final_seg_duration_list[seg_idx] < SEGMENT_MIN_IN_SECONDS:
            if seg_idx < len(final_seg_start_list) - 1 and final_seg_start_list[seg_idx] + final_seg_duration_list[seg_idx] == final_seg_start_list[seg_idx + 1]:
                # if cur segnet is adjacent with next segment
                final_seg_duration_list[seg_idx + 1] += final_seg_duration_list[seg_idx]
                final_seg_start_list[seg_idx + 1] = final_seg_start_list[seg_idx]
                final_seg_crf_list[seg_idx + 1] = min(final_seg_crf_list[seg_idx], final_seg_crf_list[seg_idx + 1])
            elif seg_idx > 0 and final_seg_start_list[seg_idx - 1] + final_seg_duration_list[seg_idx - 1] == final_seg_start_list[seg_idx]:
                # if cur segnet is adjacent with previous segment
                final_seg_duration_list[seg_idx - 1] += final_seg_duration_list[seg_idx]
                final_seg_crf_list[seg_idx - 1] = min(final_seg_crf_list[seg_idx - 1], final_seg_crf_list[seg_idx])
            else:
                assert 0, "Error: too short segment and can not be merged, will result to encoding duration error"

            final_seg_start_list.pop(seg_idx)
            final_seg_duration_list.pop(seg_idx)
            final_seg_crf_list.pop(seg_idx)
            seg_idx -= 1

        seg_idx += 1

    return final_seg_start_list, final_seg_duration_list, final_seg_crf_list

def encode_crf_final(input_video, output_video, preroll, seg_start_list, seg_duration_list, level, resolution, video_profile,
    video_filter, ffmpeg_common_settings, seg_crf_list, complex_me, gop, tune, color_str, non_ad_time_intervals, max_thread):

    assert len(seg_duration_list) == len(seg_start_list), "Length of seg_duration_list and seg_start_list are not equal."
    assert len(seg_crf_list) == len(seg_start_list), "Length of seg_crf_list and seg_start_list are not equal."

    seg_size = len(seg_start_list)
    temp_dir = tempfile.mkdtemp()
    seg_format = temp_dir + '/seg_%d.mp4'

    segment_list = []
    arg_list = []

    final_seg_start_list, final_seg_duration_list, final_seg_crf_list = \
        apply_non_ad_intervals(seg_start_list, seg_duration_list, seg_crf_list, non_ad_time_intervals)

    seg_size = len(final_seg_start_list)

    if preroll is not None and len(preroll) > 0:
        seg_name = seg_format % 0
        cur_arg = [preroll, seg_name, 0, 0, level, resolution, video_profile, video_filter, ffmpeg_common_settings,
            final_seg_crf_list[0], complex_me, gop, tune, color_str]

        arg_list.append(cur_arg)
        segment_list.append(seg_name)

    for seg_idx in range(seg_size):
        start_time = final_seg_start_list[seg_idx]
        end_time = start_time + final_seg_duration_list[seg_idx]
        seg_name = seg_format % (seg_idx + 1)
        cur_arg = [input_video, seg_name, start_time, end_time, level, resolution, video_profile, video_filter,
            ffmpeg_common_settings, final_seg_crf_list[seg_idx], complex_me, gop, tune, color_str]

        arg_list.append(cur_arg)
        segment_list.append(seg_name)

    pool = multiprocessing.Pool(processes=max_thread)
    results = pool.map_async(encode_crf_segment_unpack, arg_list).get(THREAD_TIMEOUT)
    pool.close()
    pool.join()

    success = True

    for r in results:
        if r[0] != 0:
            success = False
            break;

    if success:
        results.append(do_merge(segment_list, output_video))

    do_clean(temp_dir)
    return results
