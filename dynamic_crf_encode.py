import os
import sys
import subprocess
import tempfile
import json

common_settings = '-preset slow -b-pyramid normal -bf 3 -b_strategy 2 -err_detect compliant -mbtree 1 -tune film'
variants_path = './data/variants.json'

def get_video_profile_and_level(resolution):
    profile = None
    level = None

    with open(variants_path) as file_variants:
        variants_list = json.load(file_variants)
        for variant in variants_list:
            video_item = variant.get('video')

            if video_item is not None:
                video_width = video_item.get('width')
                video_height = video_item.get('height')

                if video_width is not None and video_height is not None:
                    if resolution == '{}x{}'.format(video_width, video_height):
                        profile  = video_item.get('profile')
                        level = video_item.get('level')
                        break;
    return profile, level

def print_usage():
    print("usage: {cmd} input_video n_split [--start-offset start_offset] [--split-len split_len]".format(cmd=sys.argv[0]))

def get_duration(input_video):
    ffprobe_cmd = "ffprobe -v error -select_streams v:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 {input_video}".format(input_video=input_video)
    return float(subprocess.check_output(ffprobe_cmd, shell=True).strip())

def encode_segment(input_video, output_video, dst_res, start_time, end_time, crf, need_deinterlacing):
    other_filter = ''

    if need_deinterlacing:
        other_filter += 'yadif,'

    v_profilie, v_level = get_video_profile_and_level(dst_res)

    ffmpeg_cmd = 'ffmpeg -hide_banner -ss {start_time} -to {end_time} -i {input_video} -filter_complex "[0:v]{other_filter}scale={dst_res}[vout]" \
-map [vout] -an -c:v libx264 {common_settings} -profile:v {v_profilie} -level {v_level} -crf {crf} -x264opts me=umh:merange=32:subme=10 -pix_fmt yuv420p -color_range tv -colorspace bt709 -color_trc bt709 -color_primaries bt709  -f mp4 {output_video} -y'.format(
                input_video=input_video,
                start_time=start_time,
                end_time=end_time,
                common_settings=common_settings,
                other_filter=other_filter,
                v_profilie=v_profilie,
                v_level=v_level,
                dst_res=dst_res,
                crf=crf,
                output_video=output_video,
            );
    print(ffmpeg_cmd)
    subprocess.call(ffmpeg_cmd, shell=True)

def do_clean(segment_list):
    for seg_video in segment_list:
        os.remove(seg_video)

def do_merge(segment_list, output_video):
    with tempfile.NamedTemporaryFile(mode="w+t") as f:
        for seg_video in segment_list:
            f.write("file '%s'\n" % seg_video)
        f.seek(0)
        print(f.read())
        ffmpeg_cmd = 'ffmpeg -hide_banner -f concat -safe 0 -i {segment_list_file}  -c copy {output_video} -y'.format(
                segment_list_file=f.name,
                output_video=output_video,
            );
        print(ffmpeg_cmd)
        subprocess.call(ffmpeg_cmd, shell=True)
        do_clean(segment_list)

def encode_final(input_video, output_video, dst_res, seg_start_list, seg_duration_list, seg_crf_list, need_deinterlacing):
    assert len(seg_duration_list), "Length of seg_duration_list and seg_start_list are not equal."
    assert len(seg_crf_list), "Length of seg_crf_list and seg_start_list are not equal."

    seg_size = len(seg_start_list)
    temp_dir = tempfile.mkdtemp()
    seg_format = temp_dir + "/seg_%d.mp4"

    segment_list = []
    for seg_idx in range(seg_size):
        start_time = seg_start_list[seg_idx]
        end_time = start_time + seg_duration_list[seg_idx]
        seg_name = seg_format % seg_idx
        encode_segment(input_video, seg_name, dst_res, start_time, end_time, seg_crf_list[seg_idx], need_deinterlacing)
        segment_list.append(seg_name)
        
    do_merge(segment_list, output_video)
    os.removedirs(temp_dir)

def get_segment_list(input_video):
    duration = get_duration(input_video)
    seg_start_list = []
    seg_duration_list = []
    seg_crf_list = []

    seg_size = 10
    for seg_idx in range(seg_size):
        seg_start_list.append(duration / seg_size * seg_idx)
        seg_duration_list.append(duration / seg_size)
        seg_crf_list.append(30 - seg_idx)

    return seg_start_list, seg_duration_list, seg_crf_list, '854x480'
    
if __name__ == '__main__':
    if len(sys.argv) < 1:
        print_usage()
        sys.exit(-1)
    
    input_video = '~/Movies/Bhavesh_60sec.mxf'
    seg_start_list, seg_duration_list, seg_crf_list, dst_res = get_segment_list(input_video)
    
    encode_final(input_video, "test.mp4", dst_res, seg_start_list, seg_duration_list, seg_crf_list, False)
