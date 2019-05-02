#!venv/bin/python
import argparse

from core.web import DPP


parser = argparse.ArgumentParser(description='Process some integers.')

parser.add_argument("start", type=str,
                    help="the starting station")
parser.add_argument("via", type=str, nargs='?', default="",
                    help='via (optional)')
parser.add_argument("end", type=str,
                    help='the final station')
parser.add_argument("-n", type=int, default=3, metavar="NUMBER",
                    help='number of connections for search')

args = parser.parse_args()

# ------------------------------------------------------------------------------ #


dpp = DPP()
title, connections = dpp.query_connection(src=args.start, dst=args.end, via=args.via, num=args.n)
