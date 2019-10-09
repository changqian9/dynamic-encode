import json
import subprocess

def parse_pts_bound(input_file):
    print 'Getting File {}  by probing frames'.format(input_file)
    cmd = "ffprobe -v quiet -select_streams v:0 -print_format json -show_format -show_entries stream -i %s" % input_file
    meta_json = parse_command_output(cmd)
    start_time = float(meta_json['format']['start_time'])
    duration = float(meta_json['format']['duration'])
    framerate_items = str(meta_json['streams'][0]['r_frame_rate']).split('/')
    fps = float(framerate_items[0]) / float(framerate_items[1])
    return start_time, duration, fps

# Parse Command Output
def parse_command_output(cmd):
    print "Running Command :" + cmd
    process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    jsonS, err = process.communicate()
    if process.returncode:
        error.set_error("Error while running command : exit code {} \n{}\n".format(str(process.returncode), str(err)))
        return None
    elif not jsonS:
        error.set_error("Error while running command : No JSON Output")
        return None
    data = json.loads(jsonS)
    return data
