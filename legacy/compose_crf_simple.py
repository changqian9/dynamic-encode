import json
import numpy as np
import argparse
import sys
import subprocess

framescores = []
composed_scores = []
last_change_frame = 0
start_time = []
duration = []
dur_crf = []
seg_num = 0

resolution = ["180", "240", "360", "480", "720", "1080"]
CRF_PHONE = ["22", "24", "26", "30"]
CRF_TV = ["20", "22", "24", "28"]
FRAME_NUM = 3
WORST_SCORE = 70
MIN_GAP_UP = 10
MAX_GAP_DOWN = 15
MIN_CHANGE_DISTANCE = 5


def get_vmafscores(file_root, res, file_type):
    vmafscores = []
    if file_type == "phone":
        for i in range(len(CRF_PHONE)):
            file_path = file_root + "_" + res + "p_" + CRF_PHONE[i] + "_phone.json"
            with open(file_path, "r") as scorefile:
                vmafscores += [json.load(scorefile)["frames"]]
    if file_type == "tv":
        for i in range(len(CRF_TV)):
            file_path = file_root + "_" + res + "p_" + CRF_TV[i] + "_tv.json"
            with open(file_path, "r") as scorefile:
                vmafscores += [json.load(scorefile)["frames"]]
    return vmafscores


def get_composed_txt(video_duration,vmafscores, file_type):
    framescores = []
    # composed_scores=[]
    last_change_frame = 0
    start_time = []
    duration = []
    dur_crf = []
    seg_num = 0
    crf_list = []
    if file_type == "phone":
        crf_list = CRF_PHONE
    if file_type == "tv":
        crf_list = CRF_TV
    for i in range(len(vmafscores[0])):
        for j in range(len(crf_list)):
            framescores += [vmafscores[j][i]["VMAF_score"]]
        if i == 0:
            ave = sum(framescores) / len(crf_list)
            distance = abs(ave - framescores[0])
            composed_score_index = 0
            for k in range(len(crf_list)):
                temp = abs(ave - framescores[k])
                if temp < distance:
                    distance = temp
                    composed_score_index = k
            # composed_score=framescores[composed_score_index]
            pre_index = composed_score_index
            start_time += [0]
        else:
            if framescores[pre_index] < WORST_SCORE:
                if (
                    pre_index > 0
                    and i < len(vmafscores[0]) - FRAME_NUM
                    and i - last_change_frame > MIN_CHANGE_DISTANCE
                ):
                    gap_up = 0
                    for k in range(FRAME_NUM):
                        if i + k < len(vmafscores[0]):
                            gap_up = (
                                gap_up
                                + vmafscores[pre_index - 1][i + k]["VMAF_score"]
                                - vmafscores[pre_index][i + k]["VMAF_score"]
                            )
                    # print("gapup"+str(gap_up))
                    if gap_up > MIN_GAP_UP:
                        composed_score_index = pre_index - 1
                        pre_index = pre_index - 1
                        # composed_score = framescores[composed_score_index]
                        last_change_frame = i
                        start_time += [i]
                        duration += [i - start_time[seg_num]]
                        dur_crf += [crf_list[composed_score_index + 1]]
                        seg_num = seg_num + 1
                        # print("up"+str(i))
                    # else:
                    #     composed_score = framescores[pre_index]
                # else:
                #     composed_score = framescores[pre_index]
            else:
                if (
                    pre_index < 3
                    and i < len(vmafscores[0]) - FRAME_NUM
                    and i - last_change_frame > MIN_CHANGE_DISTANCE
                ):
                    gap_down = 0
                    for k in range(FRAME_NUM):
                        if i + k < len(vmafscores[0]):
                            gap_down = (
                                gap_down
                                + vmafscores[pre_index][i + k]["VMAF_score"]
                                - vmafscores[pre_index + 1][i + k]["VMAF_score"]
                            )
                    # print("gapdown"+str(gap_down))
                    if gap_down < MAX_GAP_DOWN:
                        composed_score_index = pre_index + 1
                        pre_index = pre_index + 1
                        composed_score = framescores[composed_score_index]
                        last_change_frame = i
                        start_time += [i]
                        duration += [i - start_time[seg_num]]
                        dur_crf += [crf_list[composed_score_index - 1]]
                        seg_num = seg_num + 1
                        # print("down"+str(i))
                    else:
                        composed_score = framescores[pre_index]
                else:
                    composed_score = framescores[pre_index]
        # composed_scores+=[dict((('frameNum',i),('VMAF_score',composed_score),('crf',crf_phone[composed_score_index])))]
        framescores = []
        if i == len(vmafscores[0]) - 1:
            duration += [int(video_duration) - start_time[seg_num]]
            dur_crf += [crf_list[composed_score_index]]

    seg_array = np.array([start_time, duration, dur_crf])
    seg_array = seg_array.transpose()
    return seg_array

def get_duration(input_video):
    ffprobe_cmd = "ffprobe -v error -select_streams v:0 -show_entries stream=duration -of default=noprint_wrappers=1:nokey=1 {input_video}".format(input_video=input_video)
    return float(subprocess.check_output(ffprobe_cmd, shell=True).strip())

# print(type(seq_array))
# with open(video_name+'_'+resolution+'p_composed.txt','w') as outfile:
#     outfile.write(seq_array)

# save to json file
# jsonfile=dict((('seg_start_list',start_time),('seg_duration_list',duration),('seg_crf_list',dur_crf)))
# with open(video_name+'_'+resolution+'p_composed.json','w') as outfile:
#     json.dump(jsonfile,outfile)

if __name__ == "__main__":
    if len(sys.argv) < 1:
        sys.exit(-1)
    parser = argparse.ArgumentParser(description="Compose CRF in different resolution")
    parser.add_argument("input_video_root", help="Input video root.")
    parser.add_argument("output_video_folder", help="Outputt video folder.")
    args = parser.parse_args()
    file_root = (
        args.input_video_root
    )  #'/opt/videosets/analysis/0000001-Bhavesh_60sec/Bhavesh_60sec'
    video_duration=get_duration(file_root + "_" + resolution[0] + "p_" + CRF_PHONE[0] +".mp4")
    for i in range(len(resolution)):
        vmafscores = get_vmafscores(file_root, resolution[i], "phone")
        seg_array = get_composed_txt(video_duration,vmafscores, "phone")
        np.savetxt(
            args.output_video_folder + "/" + resolution[i] + "p_phone.txt",
            seg_array,
            fmt="%s",
            delimiter=",",
        )
        vmafscores = get_vmafscores(file_root, resolution[i], "tv")
        seg_array = get_composed_txt(video_duration,vmafscores, "tv")
        np.savetxt(
            args.output_video_folder + "/" + resolution[i] + "p_tv.txt",
            seg_array,
            fmt="%s",
            delimiter=",",
        )
