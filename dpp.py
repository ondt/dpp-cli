#!venv/bin/python
import argparse

from core.web import DPP


parser = argparse.ArgumentParser(description="Find connections for Prague public transport.")
parser.add_argument("start", type=str,
                    help="the starting station")
parser.add_argument("via", type=str, nargs="?", default="",
                    help="via (optional)")
parser.add_argument("end", type=str,
                    help="the final station")
parser.add_argument("-n", type=int, default=3, metavar="NUMBER",
                    help="number of connections for search (default = 3)")

args = parser.parse_args()

# ------------------------------------------------------------------------------ #


dpp = DPP()
title, connections = dpp.query_connection(src=args.start, dst=args.end, via=args.via, num=args.n)

print(title)
print()

for connection in connections:
	print(f"\033[1m{connection.summary}\033[0m")

	for step in connection.steps:
		print(f"\t{step}")

	print()
