import os
import json, re, fractions
import subprocess
from utils import error
from log import logger
import tempfile


# Parse JSON File
def parse_json(file_name):
    try:
        fp = open(file_name, "r")
        data = json.load(fp)
        fp.close()
        return data
    except Exception as e:
        logger.exception(e)
    return {}

# Parse Video
def parse_tracks(input_file):
    if not os.path.exists(input_file):
        logger.error("Input file :{} not found".format(input_file))
        error.set_error("Input file :{} not found".format(input_file))
        return None
    logger.info("Parsing input file %s" % input_file)
    cmd = "ffprobe  -v quiet -print_format json -show_format -show_streams -hide_banner -i %s" % input_file
    return parse_command_output(cmd)


# Parse Video
def parse_video(input_file):
    if not os.path.exists(input_file):
        logger.error("Input file :{} not found".format(input_file))
        error.set_error("Input file :{} not found".format(input_file))
        return None
    logger.info("Parsing input file %s" % input_file)
    cmd = "ffprobe -show_streams -select_streams v:0 -show_entries format_tags=timecode -print_format json -i %s" % input_file
    return parse_command_output(cmd)


# Parse Audio
def parse_audio(input_file):
    if not os.path.exists(input_file):
        logger.error("Input file :{} not found".format(input_file))
        error.set_error("Input file :{} not found".format(input_file))
        return None
    logger.info("Parsing input file %s" % input_file)
    cmd = "ffprobe -v quiet -select_streams a -show_entries stream=index -of csv -print_format json -i  %s" % input_file
    return parse_command_output(cmd)

def parse_audio_channel_info(input_file):
    if not os.path.exists(input_file):
        logger.error("Input file :{} not found".format(input_file))
        error.set_error("Input file :{} not found".format(input_file))
        return None
    logger.info("Parsing input file %s" % input_file)
    cmd = "ffprobe -v quiet -select_streams a -show_entries stream=channels -of csv -print_format json -i  %s" % input_file
    return parse_command_output(cmd)

# Parse Start end seconds
def parse_start_end_seconds(star_end_list):
    start_end_seconds = []
    if star_end_list:
        for entry in star_end_list:
            for l in entry.split(';'):
                start_end_seconds.append(l.split(','))
    return start_end_seconds


def parse_duration(input_file, method='metadata'):
    try:
        if method == 'last_frame':
            logger.info('Getting File {} Duration by probing last frame'.format(input_file))
            cmd = "ffprobe -v quiet -select_streams v:0 -show_packets -show_entries packet=dts_time -of csv=p=0 -print_format json -i  %s" % input_file
            dts_data = parse_command_output(cmd)
            duration = float(dts_data['packets'][-1]['dts_time']) - float(dts_data['packets'][0]['dts_time'])
        elif method == 'decode':
            logger.info('Getting File {} Duration by decoding the whole file'.format(input_file))
            duration = parse_duration_by_decode(input_file)
        else:
            logger.info('Getting File {} Duration from metadata'.format(input_file))
            cmd = "ffprobe -v quiet -select_streams v:0 -print_format json -show_format -i %s" % input_file
            duration_data = parse_command_output(cmd)
            duration = float(duration_data['format']['duration'])
        logger.info('File {} duration is {}'.format(input_file, duration))
        return duration
    except Exception as e:
        logger.exception('Unable to get duration')
        return 0


# Parse Command Output
def parse_command_output(cmd):
    logger.debug("Running Command :" + cmd)
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


# Parse ffmpeg logger files for HES logs
def parse_ffmpeg_logger(file_name):
    fp = open(file_name, "r")
    res = []
    for line in fp:
        line = line.rstrip('\n')
        tok = re.findall('.*\[hes\].+', line)
        if len(tok) > 0:
            res.append(tok[0])
    return res


def get_sec(time_str):
    h, m, s, f= time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)


# Getting duration by decoding the file to handle file corrupt case
def parse_duration_by_decode(input_file):
    logger.info('Getting File {} Duration by decoding it'.format(input_file))
    temp_file, temp_file_name = tempfile.mkstemp(suffix=".txt")
    ffmpeg_cmd = "ffmpeg -i %s -vstats_file %s -f null -" % (input_file, temp_file_name)
    logger.info('FFMPEG command {}'.format(ffmpeg_cmd))
    ret = subprocess.call(ffmpeg_cmd, shell=True)
    if ret == 0:
        try:
            with open(temp_file_name, "rb") as f:
                f.seek(-2, os.SEEK_END)
                while f.read(1) != b'\n':
                    f.seek(-2, os.SEEK_CUR)
                line = f.readline().decode()
                data = re.findall(r'.*time= ([0-9.]+)', line)
                return float(data[0])
        except Exception:
            logger.info('Decoded duration cannot be extracted. Setting duration to 0')
    else:
        logger.info('FFMPEG decode error. Cannot fetch duration. Setting duration to 0')
    return 0

def parse_dar_from_resolution(width, height):
    #Assumes SAR = 1:1
    dar = ''
    f = fractions.Fraction(width, height)
    if f:
        dar = str(f).replace('/', ':')
    return dar

