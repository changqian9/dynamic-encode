#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os
import tempfile
import subprocess, multiprocessing

from tool import do_merge, do_clean

def encode_crf_segment(input_video, output_video, start_time, end_time, level, resolution, video_profile, video_filter, ffmpeg_common_settings, crf, complex_me, gop, tune, color_str, audio_codec_and_samplerate, audio_profile, audio_channel, audio_bitrate, audio_filter):
    # set audio codec, aac for aac_low, libfdk_aac for aac_he and aac_he_v2
    x264_other_opt = ":me=umh:merange=32:subme=10"

    ffmpeg_cmd = 'ffmpeg -ss {START_TIME} -to {END_TIME} -i {INPUT_VIDEO} -filter_complex "[0:v]{V_FILTER}scale={RESOLUTION}[vout]{A_FILTER}" \
            -map [vout] -map [aout] {FFMPEG_COMMON_SETTINGS} -level {LEVEL} -profile:v {V_PROFILE} -crf {CRF} -tune {TUNE} {A_CODEC_AND_SAMPLERATE} -profile:a {A_PROFILE} -ac {A_CHANNEL} -b:a {A_BITRATE}k -x264opts no-scenecut:keyint={GOP}:min-keyint={GOP}{X264_OTHER_OPT} -pix_fmt yuv420p {COLOR_STR} -f mp4 {OUTPUT_VIDEO} -y'.format(
                INPUT_VIDEO=input_video,
                START_TIME=start_time,
                END_TIME=end_time,
                FFMPEG_COMMON_SETTINGS=ffmpeg_common_settings,
                LEVEL=level,
                V_FILTER=video_filter,
                V_PROFILE=video_profile,
                RESOLUTION=resolution,
                CRF=crf,
                GOP=gop,
                TUNE=tune,
                A_CODEC_AND_SAMPLERATE=audio_codec_and_samplerate,
                A_PROFILE=audio_profile,
                A_CHANNEL=audio_channel,
                A_BITRATE=audio_bitrate,
                A_FILTER=audio_filter,
                COLOR_STR=color_str,
                X264_OTHER_OPT=x264_other_opt if complex_me else "",
                OUTPUT_VIDEO=output_video,
            )

    print(ffmpeg_cmd)

    ret = subprocess.call(ffmpeg_cmd, shell=True)
    if ret != 0:
        return None
    return output_video

def encode_crf_segment_unpack(args):
    return encode_crf_segment(*args)

def encode_crf_final(input_video, output_video, seg_start_list, seg_duration_list, level, resolution, video_profile, video_filter, ffmpeg_common_settings, seg_crf_list, complex_me, gop, tune, color_str, audio_codec_and_samplerate, audio_profile, audio_channel, audio_bitrate, audio_filter, max_thread):
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
        cur_arg = [input_video, seg_name, start_time, end_time, level, resolution, video_profile, video_filter, ffmpeg_common_settings, seg_crf_list[seg_idx], complex_me, gop, tune, color_str, audio_codec_and_samplerate, audio_profile, audio_channel, audio_bitrate, audio_filter]

        arg_list.append(cur_arg)
        segment_list.append(seg_name)

    pool = multiprocessing.Pool(processes=max_thread)
    pool.map(encode_crf_segment_unpack, arg_list)
    pool.close()
    pool.join()
    do_merge(segment_list, output_video)
    do_clean(segment_list)
    os.removedirs(temp_dir)


