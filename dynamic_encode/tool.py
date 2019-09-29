#!/usr/bin/env python
# -*- coding: UTF-8 -*-
import os, sys
import shutil, glob
import tempfile
import subprocess
def do_clean(to_remove_dir):
    shutil.rmtree(to_remove_dir)

def remove_segments(segment_list):
    for seg_file in segment_list:
        os.remove(seg_file)

def do_merge(segment_list, output_video):
    with tempfile.NamedTemporaryFile(mode="w+t", dir=".", prefix="concat_seg_list") as f:
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

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "%s output_video seg_0 seg_1 ..." % sys.argv[0]
        exit(0)
    output_video = sys.argv[1]
    segment_list = sys.argv[2:]
    ret, msg = do_merge(segment_list, output_video)
    print msg
