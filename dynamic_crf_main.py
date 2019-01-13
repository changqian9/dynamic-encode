#!/usr/bin/env python
import sys
import json, argparse

import subprocess
from dynamic_encode import encode_final

COMMON_VIDEO_QUALITY_SETTINGS = '-vsync 0 -c:v libx264 -preset slow -psnr -b-pyramid normal -bf 3 -b_strategy 2 -err_detect compliant -mbtree 1 '

def is_number(str):
    try:
        if str=='NaN':
            return False
        float(str)
        return True
    except ValueError:
        return False

def get_duration(input_video):
    ffprobe_cmd = "ffprobe -v error -select_streams v:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 {input_video}".format(input_video=input_video)
    return float(subprocess.check_output(ffprobe_cmd, shell=True).strip())

def get_video_profile_and_level(v_height):
    profile = None
    level = None
    resolution = ''
    variant_string = '[{ "audio": { "profile": "aac_he", "channel": 1, "bitrate": 16, "codec": "mp4a.40.5" }, "video": { "width": 320, "height": 180, "profile": "baseline", "level": "1.2", "codec": "avc1.42C00C" }}, { "audio": { "profile": "aac_he", "channel": 2, "bitrate": 32, "codec": "mp4a.40.5" }, "video": { "width": 426, "height": 240, "profile": "baseline", "level": "2.1", "codec": "avc1.42C015" }}, { "audio": { "profile": "aac_he", "channel": 2, "bitrate": 32, "codec": "mp4a.40.5" }, "video": { "width": 640, "height": 360, "profile": "main", "level": "3", "codec": "avc1.4D401E" }}, { "audio": { "profile": "aac_he", "channel": 2, "bitrate": 48, "codec": "mp4a.40.5" }, "video": { "width": 854, "height": 480, "profile": "main", "level": "3.1", "codec": "avc1.4D401F" }}, { "audio": { "profile": "aac_he", "channel": 2, "bitrate": 48, "codec": "mp4a.40.5" }, "video": { "width": 1280, "height": 720, "profile": "main", "level": "3.1", "codec": "avc1.4D401F" }}, { "audio": { "profile": "aac_he", "channel": 2, "bitrate": 64, "codec": "mp4a.40.5" }, "video": { "width": 1920, "height": 1080, "profile": "high", "level": "4", "codec": "avc1.640028" }}]'
    variants_list = json.loads(variant_string)
    for variant in variants_list:
        video_item = variant.get('video')

        if video_item is not None:
            video_width = video_item.get('width')
            video_height = video_item.get('height')

            if video_width is not None and video_height is not None:
                if str(v_height) == str(video_height):
                    profile  = video_item.get('profile')
                    level = video_item.get('level')
                    resolution = "{}x{}".format(video_width, v_height)
                    break
    return profile, level, resolution

def get_segment_list_equal_duration(input_video, seg_size = 10):
    duration = get_duration(input_video)
    seg_start_list = []
    seg_duration_list = []
    seg_crf_list = []
 
    for seg_idx in range(seg_size):
        seg_start_list.append(duration / seg_size * seg_idx)
        seg_duration_list.append(duration / seg_size)
        seg_crf_list.append(30 - seg_idx)

    return seg_start_list, seg_duration_list, seg_crf_list

def get_segment_list_from_file(list_file, fixed_crf):
    seg_start_list = []
    seg_duration_list = []
    seg_crf_list = []
    segment_list_lines = []
    with open(list_file, 'r') as f:
        segment_list_lines = f.readlines()
    for segment_line in segment_list_lines:
        if segment_line.startswith('#'):
            continue
        seg_items = [item.strip() for item in segment_line.split(',')]
        if len(seg_items) == 3 and is_number(seg_items[0]) and is_number(seg_items[1]) and is_number(seg_items[2]):
            seg_start_list.append(float(seg_items[0]))
            seg_duration_list.append(float(seg_items[1]))
            seg_crf_list.append(float(seg_items[2]) if fixed_crf == 0 else fixed_crf)
    return seg_start_list, seg_duration_list, seg_crf_list

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Dynamic CRF encoding')
    parser.add_argument('input_video', help='Input video file path.')
    parser.add_argument('output_video', help='Output video file path.')
    parser.add_argument('output_height', help='Output video height.')
    parser.add_argument('segment_list', help='Segment crf list file, line format: seg_start, seg_duration, seg_crf')
    parser.add_argument('--ref-scan-type', dest='ref_scan_type', help="Ref video scan type. interlaced or progressive", default="progressive")
    parser.add_argument('--max-thread', dest='max_thread', help="Max threads to run splitted encoding", type=int, default=12)
    parser.add_argument('--complex-me', dest='complex_me', help="Use more complex(but slower) -me x264 options to encode", action="store_true", default=False)
    parser.add_argument('--fixed-crf', dest='fixed_crf', help="Use fixed crf value instead of settings in segment_list. default 0(do not use)", type=int, default=0)
    parser.add_argument('--gop', dest='gop', help="GOP x264 option for final encoding. default 50", type=int, default=50)
    args = parser.parse_args()

    seg_start_list, seg_duration_list, seg_crf_list = get_segment_list_from_file(args.segment_list, args.fixed_crf)
    v_profile, v_level, v_resolution = get_video_profile_and_level(args.output_height)

    encode_final(args.input_video, args.output_video, v_profile, v_level, v_resolution, seg_start_list, seg_duration_list, COMMON_VIDEO_QUALITY_SETTINGS, seg_crf_list, args.ref_scan_type == "interlaced", args.complex_me, args.gop, min(args.max_thread, len(seg_start_list)))
