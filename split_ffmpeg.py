#!/usr/bin/env python
#
import os
import re
import pprint
import sys
from pathlib import Path
import subprocess as sp
from os.path import basename
from subprocess import *
from optparse import OptionParser


def parseChapters(filename):
    chapters = []
    command = ["ffmpeg", '-i', filename]
    output = ""
    m = None
    title = None
    chapter_match = None
    try:
        # ffmpeg requires an output file and so it errors
        # when it does not get one so we need to capture stderr,
        # not stdout.
        output = sp.check_output(command, stderr=sp.STDOUT, universal_newlines=True)
    except CalledProcessError as e:
        output = e.output
    num = 1

    for line in iter(output.splitlines()):
        x = re.match(r".*title.*: (.*)", line)
        print("x:")
        pprint.pprint(x)

        print("title:")
        pprint.pprint(title)

        m1 = None
        if x is None:
            m1 = re.match(r".*Chapter #(\d+:\d+): start (\d+\.\d+), end (\d+\.\d+).*", line)
            title = None
        else:
            title = x.group(1)

        if m1 is not None:
            chapter_match = m1

        print("chapter_match:")
        pprint.pprint(chapter_match)

        if title != None and chapter_match != None:
            m = chapter_match
            pprint.pprint(title)
        else:
            m = None

        if m is not None:
            chapters.append({"name": repr(num) + " - " + title, "start": m.group(2), "end": m.group(3)})
            num += 1

    return chapters


def getChapters():
    parser = OptionParser(usage="usage: %prog [options] [FILE]...", version="%prog 1.0")
    parser.add_option("-f", "--force", action="store_true", dest="overwrite", \
                      help="Force overwrite")
    #  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", help="Verbose")
    #  parser.add_option("-q", "--quiet", action="store_false", dest="verbose", help="Quiet")
    parser.add_option("-d", "--dir", dest="dir", help="Output directory")

    (options, args) = parser.parse_args()
    for infile in args:
        fbase, fext = os.path.splitext(infile)
        if options.dir is None:
            path = os.path.dirname(infile)
        else:
            path = options.dir

        newdir = os.path.join(path, fbase)

        # Make the directory for output
        try:
            os.mkdir(newdir)
        except FileExistsError:
            if not options.overwrite:
                print(f"Output directory {newdir} already exists, use -f option to force overwrite")
                sys.exit(1)
            else:
                pass

        chapters = parseChapters(infile)

        for chap in chapters:
            chap['name'] = chap['name'].replace('/', ':')
            chap['name'] = chap['name'].replace("'", "\'")
            print("start:" + chap['start'])
            chap['title'] = chap['name']
            reg_path = re.sub("[^-a-zA-Z0-9_.():' ]+",'', chap['name']) + fext
            chap['outfile'] = os.path.join(str(newdir), reg_path)
            print(chap['outfile'])
            chap['origfile'] = infile
            print(chap['outfile'])
        return chapters

def convertChapters(chapters):
    for chap in chapters:
        print("start:" + chap['start'])
        print(chap)
        command = [
            "ffmpeg", '-i', chap['origfile'],
            '-vcodec', 'copy',
            '-acodec', 'copy',
            '-metadata', "title=%s" % chap['title'],
            '-ss', chap['start'],
            '-to', chap['end'],
            chap['outfile']]
        output = ""
        try:
            # ffmpeg requires an output file and so it errors
            # when it does not get one
            output = sp.check_output(command, stderr=sp.STDOUT, universal_newlines=True)
        except CalledProcessError as e:
            output = e.output
            raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))


if __name__ == '__main__':
    chaps = getChapters()
    convertChapters(chaps)
