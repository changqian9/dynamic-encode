import os, sys
import json, tempfile
import subprocess, multiprocessing
from utils.parser import parse_pts_bound
from dynamic_encode.tool import do_merge, do_clean, remove_segments

DELETE_TEMP = False
PROCESS_COUNT = 10
PROCESS_TIMEOUT = 7* 24 * 60 * 60

def generate_seg_info(source_video):
    cur_start, total_dur, fps = parse_pts_bound(source_video)
    return cur_start, 4, total_dur, fps

def ffmpeg_worker(cmd):
    return os.popen(cmd).read()

def calc_vmaf(source_video, output_video, work_dir, need_deinterlace = False, subsample = 25, pool = "mean"):
    ret = {}
    output_items = os.path.splitext(output_video)
    vmaf_output = "%s.json" % (output_items[0])

    libvmaf_cmd = "ffmpeglibvmaf 1920 1080 {INPUT} {OUTPUT} --work-dir {WORK_DIR} --subsample {SUBSAMPLE} --pool {POOL} --out-fmt json".format(INPUT=source_video, OUTPUT=output_video, WORK_DIR=work_dir, SUBSAMPLE = subsample, POOL = pool)

    if need_deinterlace:
        libvmaf_cmd += " --ref-scan-type interlaced"
    libvmaf_cmd += " > " + vmaf_output
    subprocess.call(libvmaf_cmd, shell=True)
    print libvmaf_cmd
    with open(vmaf_output) as f:
        vmaf_json = json.load(f)
    ret["vmaf_score"] = vmaf_json['aggregate']['VMAF_score']
    ret["psnr_score"] = vmaf_json['aggregate']['PSNR_score']
    ret["ssim_score"] = vmaf_json['aggregate']['SSIM_score']
    return ret

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print "%s source_file output_video" % sys.argv[0]
        exit(0)

    source_video = sys.argv[1]
    output_video = sys.argv[2]

    work_dir = os.path.dirname(output_video) or "."
    cur_start, seg_dur, total_dur, video_fps = generate_seg_info(source_video)

    idx = 0
    enccmd_list = []
    segment_list = []
    shot_tmp_dir = tempfile.mkdtemp(suffix='', prefix='shot_', dir=work_dir)
    while cur_start < total_dur:
        cur_dur = min(seg_dur, total_dur - cur_start)
        seg_file = "%s/%d_%d.webm" % (shot_tmp_dir, idx, int(cur_start * 25))
        num_frame = round(cur_dur * video_fps)
        gop = num_frame
        cmd = 'time ffmpeg -hide_banner -xerror -v warning -nostdin -ss {START_TIME} -i {SOURCE_VIDEO} -vframes {NUM_FRAME} -filter_complex "[0:v]yadif,scale=960x540[vout]" -map [vout] -vsync 0 -muxdelay 0 -aspect 16:9 -pix_fmt yuv420p -color_range tv -colorspace bt709 -color_trc bt709 -color_primaries bt709 -c:v libvpx-vp9 -quality good -speed 1 -lag-in-frames 25 -auto-alt-ref 1 -arnr-maxframes 4 -qmin 10 -row-mt 1 -dash 0 -profile:v 0 -level 3.1 -sc_threshold 0 -tune-content film -g {GOP} -keyint_min {GOP} -threads 12 -crf 37 -b:v 813k -tile-columns 0 -f webm {OUTPUT_VIDEO} -y'.format(START_TIME=cur_start, SOURCE_VIDEO=source_video, NUM_FRAME=num_frame, GOP=gop,  OUTPUT_VIDEO=seg_file)
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
    vmaf_ret = calc_vmaf(source_video, output_video, work_dir, True)
    if DELETE_TEMP:
        remove_segments(segment_list)
        do_clean(shot_tmp_dir)

    print vmaf_ret
