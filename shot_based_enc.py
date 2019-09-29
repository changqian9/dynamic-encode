import os, sys
import subprocess, multiprocessing
from utils.parser import parse_duration
from dynamic_encode.tool import do_merge

start_offset = 0.0

PROCESS_COUNT = 10
PROCESS_TIMEOUT = 7* 24 * 60 * 60

def generate_seg_info(source_video, seg_count):
    total_dur = parse_duration(source_video, "last_frame")
    seg_dur = total_dur / seg_count
    cur_start = start_offset
    return cur_start, seg_dur, total_dur

def ffmpeg_worker(cmd):
    return os.popen(cmd).read()

if __name__ == '__main__':
    if len(sys.argv) < 4:
        print "%s source_file seg_count output_video" % sys.argv[0]
        exit(0)

    source_video = sys.argv[1]
    seg_count = int(sys.argv[2])
    output_video = sys.argv[3]

    cur_start, seg_dur, total_dur = generate_seg_info(source_video, seg_count)

    idx = 0
    enccmd_list = []
    segment_list = []
    while cur_start < total_dur - 0.01:
        cur_dur = min(seg_dur, total_dur - cur_start)
        seg_file = "shot/%d_%d.webm" % (idx, int(cur_start * 25))
        cmd = 'time ffmpeg -hide_banner -xerror -v warning -nostdin -ss %f -i %s -filter_complex "[0:v]yadif,scale=960x540[vout]" -t %f  -map [vout] -vsync 2 -muxdelay 0 -aspect 16:9 -pix_fmt yuv420p -color_range tv -colorspace bt709 -color_trc bt709 -color_primaries bt709 -c:v libvpx-vp9 -quality good -speed 1 -lag-in-frames 25 -auto-alt-ref 1 -b_qfactor 1.3 -arnr-maxframes 4 -qmin 10 -row-mt 1 -dash 0 -profile:v 0 -level 3.1 -g 50 -keyint_min 50 -sc_threshold 0 -tune-content film -seg-dur 4.0 -threads 12 -crf 37 -b:v 813k -tile-columns 0 -avoid_negative_ts 1 -f webm %s -y' % (cur_start, source_video, cur_dur, seg_file)
        segment_list.append(seg_file)
        enccmd_list.append(cmd)
        print cmd
        cur_start += cur_dur
        idx += 1

    pool = multiprocessing.Pool(processes=PROCESS_COUNT)
    results = pool.map_async(ffmpeg_worker, enccmd_list).get(PROCESS_TIMEOUT)
    pool.close()
    pool.join()
    print segment_list
    ret, msg = do_merge(segment_list, output_video)
    print msg
