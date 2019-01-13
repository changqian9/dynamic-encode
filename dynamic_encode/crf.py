#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import subprocess

def encode_crf_segment(input_video, output_video, v_profilie, v_level, resolution, start_time, end_time, ffmpeg_common_settings, crf, need_deinterlacing, complex_me, gop):
    other_filter = ''

    if need_deinterlacing:
        other_filter += 'yadif,'

    x264_other_opt = ":me=umh:merange=32:subme=10"
    ffmpeg_cmd = 'ffmpeg -hide_banner -ss {start_time} -to {end_time} -i {input_video} -filter_complex "[0:v]{other_filter}scale={dst_res}[vout]" \
            -map [vout] {ffmpeg_common_settings} -tune film -profile:v {v_profilie} -level {v_level} -crf {crf} -x264opts no-scenecut:keyint={gop}:min-keyint={gop}{x264_other_opt} -pix_fmt yuv420p -color_range tv -colorspace bt709 -color_trc bt709 -color_primaries bt709  -f mp4 {output_video} -y'.format(
                input_video=input_video,
                start_time=start_time,
                end_time=end_time,
                ffmpeg_common_settings=ffmpeg_common_settings,
                other_filter=other_filter,
                v_profilie=v_profilie,
                v_level=v_level,
                dst_res=resolution,
                crf=crf,
                gop=gop,
                x264_other_opt=x264_other_opt if complex_me else "",
                output_video=output_video,
            )
    print(ffmpeg_cmd)
    subprocess.call(ffmpeg_cmd, shell=True)


