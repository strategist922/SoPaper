#!/usr/bin/env python2
# -*- coding: UTF-8 -*-
# File: pdfprocess.py
# Date: Thu May 22 15:53:05 2014 +0800
# Author: Yuxin Wu <ppwwyyxxc@gmail.com>

import tempfile
import os
from bson.binary import Binary

from uklogger import *
from ukdbconn import get_mongo
from ukutil import check_pdf
from lib.pdf2html import PDF2Html
from lib.textutil import parse_file_size

def do_addhtml(data, pid):
    # convert to html
    converter = PDF2Html(data, filename=None)
    npage = converter.get_npages()
    htmls = [converter.get(x) for x in range(npage + 1)]
    converter.clean()

    db = get_mongo('paper')
    db.update({'_id': pid}, {'$set': {'page': npage, 'html': htmls}})
    log_info("Add html for pdf {0}, page={1}".format(pid, npage))

def pdf_compress(data):
    """ take a pdf data string, return a compressed string
        compression is done using ps2pdf14 in ghostscript
    """
    f = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    log_info("Start compressing with {0} ...".format(f.name))
    f.write(data)
    f.close()

    f2 = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    f2.close()
    os.system('ps2pdf14 "{0}" "{1}"'.format(f.name, f2.name))

    newdata = open(f2.name).read()
    os.remove(f2.name)
    os.remove(f.name)
    if len(newdata) < len(data) and check_pdf(newdata):
        log_info("Compress succeed: {0}->{1}".format(
            parse_file_size(len(data)), parse_file_size(len(newdata))))
        return newdata
    else:
        return data

def do_compress(data, pid):
    # compress
    data = pdf_compress(data)

    db = get_mongo('paper')
    db.update({'_id': pid}, {'$set': {'pdf': Binary(data)}} )
    log_info("Updated compressed pdf {0}: size={1}".format(
        pid, parse_file_size(len(data))))

def pdf_postprocess(data, pid):
    """ post-process routine right after adding a new pdf"""
    do_compress(data, pid)
    do_addhtml(data, pid)