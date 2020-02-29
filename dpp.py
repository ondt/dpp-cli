#!venv/bin/python
import argparse
import json
import sys

from core.web import DPP



class ArgumentParser(argparse.ArgumentParser):
	def error(self, message):
		raise argparse.ArgumentError(None, message)



# parser = ArgumentParser(description="Find connections for Prague public transport.")
parser = argparse.ArgumentParser(description="Find connections for Prague public transport.")
parser.add_argument("start", type=str, help="the starting station")
parser.add_argument("via", type=str, nargs="?", default="", help="via (optional)")
parser.add_argument("end", type=str, help="the final station")
parser.add_argument("-n", type=int, default=3, metavar="NUMBER", help="number of connections for search (default: 3)")
parser.add_argument("-f", type=str, choices=["pretty", "json", "pdf"], default="pretty", help="output format (default: pretty)")

##########################################################

if __name__ == '__main__':
	dpp = DPP()
	args = parser.parse_args()

	if args.f == "pdf":
		pdf = dpp.pdf(from_stop=args.start, to_stop=args.end, via_stop=args.via, num=args.n)
		sys.stdout.buffer.write(pdf)

	else:
		title, connections = dpp.query_connection(from_stop=args.start, to_stop=args.end, via_stop=args.via, num=args.n, show_progress=args.f == "pretty")

		if args.f == "pretty":
			print(title, "\n")
			print(dpp.connections_to_str(connections))

		if args.f == "json":
			print(json.dumps({
				"title":       title,
				"connections": dpp.connections_to_json(connections),
			}))
