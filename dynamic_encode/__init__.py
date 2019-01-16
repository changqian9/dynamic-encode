#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from crf import encode_crf_final
from tool import do_clean, do_merge

if __name__ == '__main__':
    print("A package that dynmaically encodes videos using variable ffmpeg params")
else:
    __all__ = [ 'encode_crf_final', 'do_clean', 'do_merge' ]
