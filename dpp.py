#!venv/bin/python
import argparse

from core.web import DPP



class ArgumentParser(argparse.ArgumentParser):
	def error(self, message):
		raise argparse.ArgumentError(None, message)



parser = ArgumentParser(description="Find connections for Prague public transport.")
parser.add_argument("start", type=str, help="the starting station")
parser.add_argument("via", type=str, nargs="?", default="", help="via (optional)")
parser.add_argument("end", type=str, help="the final station")
parser.add_argument("-n", type=int, default=3, metavar="NUMBER", help="number of connections for search (default n = 3)")  # default=3
parser.add_argument("-f", type=str, default="pretty", metavar="FORMAT", help="output format (pretty, json, pdf) (default = pretty)")  # todo: choose

##########################################################

if __name__ == '__main__':
	dpp = DPP()
	args = parser.parse_args()

	title, connections = dpp.query_connection(from_stop=args.start, to_stop=args.end, via_stop=args.via, num=args.n)

	print(title)
	print()
	print(dpp.connections_to_str(connections))
