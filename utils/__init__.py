import os
import sys
import json
import config
import shutil
import datetime
import time


# get recursive dict key and check against value
def dict_match(obj, key, val):
    parts = key.split("/")
    key = parts.pop(-1)
    for part in parts:
        if not part:
            continue
        if not obj:
            return False
        obj = obj.get(part)
    if not obj:
        return False
    return obj.get(key) == val


def get_timestmap_appended_file_name(filename):
    file_vector = os.path.splitext(filename)
    timestamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%dT%H-%M-%S')
    return "{}-{}{}".format(file_vector[0], timestamp, file_vector[1])


# Create Directory
def create_dir(work_directory):
    if not os.path.isdir(work_directory):
        original_umask = 0
        try:
            original_umask = os.umask(0)
            os.makedirs(work_directory, 0777)
        except OSError as e:
            print "Error in create_dir", e
            pass
        finally:
            os.umask(original_umask)


# Special exit function which provides xcom friendly error messages
def hs_exit(code, value=None):
    time.sleep(10)
    value = value if value else "Unknown"
    data = json.dumps({'status': 'failed' if code else 'success', 'code': code, 'value': value})
    dname = os.path.dirname(config.EXIT_STATUS_FILE)
    # Check if dir exists
    if not dname or not os.path.isdir(dname):
        print dname, "does not exists, not writing exit status to :", config.EXIT_STATUS_FILE
    else:
        try:
            with open(config.EXIT_STATUS_FILE, 'w') as fp:
                fp.write(data)
                fp.flush()
        except IOError as e:
            print "IO Error while writing exit status to file :", config.EXIT_STATUS_FILE, str(e)
        except Exception as e:
            # Ignore the exception
            print "Exception while writing exit status to file :", config.EXIT_STATUS_FILE, str(e)
    # this shoulld be the last line
    print data
    sys.exit(code)


def delete_dir(dir_name):
    print "Deleting Dir", dir_name
    try:
        shutil.rmtree(dir_name)
    except Exception as e:
        print "Exception in deleting dir ", dir_name, str(e)


def copy_file(current_filepath, new_filepath):
    if os.path.exists(current_filepath):
        shutil.copyfile(current_filepath, new_filepath)
    else:
        return None
    return new_filepath
