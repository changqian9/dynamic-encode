#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import shutil
import tempfile
import subprocess
def do_clean(to_remove_dir):
    shutil.rmtree(to_remove_dir)

def do_merge(segment_list, output_video):
    with tempfile.NamedTemporaryFile(mode="w+t") as f:
        for seg_video in segment_list:
            f.write("file '%s'\n" % seg_video)
        f.seek(0)
        ffmpeg_cmd = 'ffmpeg -hide_banner -xerror -v warning -nostdin -f concat -safe 0 -i {segment_list_file} -c copy {output_video} -y'.format(
                segment_list_file=f.name,
                output_video=output_video,
            )
        ret = subprocess.call(ffmpeg_cmd, shell=True)
        return ret, ffmpeg_cmd + "\n" + f.read()
    return -1, "do_merge"
