#!/usr/bin/env python3
"""Turn the video title into a file name, so videos on different topics never share a name.

  topic_name.py out/publish.txt          # uses the first line (the title) of publish.txt
  topic_name.py --title "豆包和 WorkBuddy 要不要付费？"

Spaces are dropped, punctuation becomes "-", the result is at most 40 characters.
  豆包和 WorkBuddy 要不要付费？ -> 豆包和WorkBuddy要不要付费
  AI 提问模板：说清四件事，一次写对 -> AI提问模板-说清四件事-一次写对
Use it as out/<name>.mp4 and out/<name>-封面.png.
"""
import argparse, re


def topic_name(title):
    s = re.sub(r'\s+', '', title.strip())
    s = re.sub(r'[^\w一-鿿]+', '-', s)        # punctuation, slashes, quotes -> -
    return s.strip('-')[:40].rstrip('-') or 'video'


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('publish', nargs='?', help='publish.txt; its first non-empty line is the title')
    ap.add_argument('--title')
    a = ap.parse_args()
    title = a.title or next(l for l in open(a.publish, encoding='utf-8') if l.strip())
    print(topic_name(title))


if __name__ == '__main__':
    main()
