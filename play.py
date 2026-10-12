#!/usr/bin/env python3
"""SAILINGSTONE QUEST — 세일링스톤 AI-BI 인턴 수습 시뮬레이션 (SQL + Python 학습 게임)

사용법: python play.py [명령]
명령 목록: python play.py help
"""
import sys

if sys.version_info < (3, 8):
    sys.exit("Python 3.8 이상이 필요해요. 지금 버전: " + sys.version.split()[0])

from quest.engine import main

if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print()
