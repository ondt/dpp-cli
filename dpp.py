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
parser.add_argument("-n", type=int, metavar="NUMBER", help="number of connections for search (default n = 3)")  # default=3
parser.add_argument("-f", type=str, default="pretty", metavar="FORMAT", help="output format (pretty, json, pdf) (default = pretty)")  # todo: choose
parser.add_argument("-s", "--stats", action="store_true", help="print connection statistics (default n = 32)")  # todo: next hour, not n connections

##########################################################

if __name__ == '__main__':
	dpp = DPP()
	args = parser.parse_args()

	# default n
	if args.n is None:
		args.n = 32 if args.stats else 3

	if not args.stats:
		title, connections = dpp.query_connection(from_stop=args.start, to_stop=args.end, via_stop=args.via, num=args.n)

		print(title)
		print()

		print(dpp.connections_to_str(connections))


	else:
		title, connections, best_conn, worst_conn, min_time, max_time, avg_time = dpp.stats(src=args.start, dst=args.end, via=args.via, num=args.n)

		print(title)
		print()

		print(f"connections: {connections}")
		print(f"min time: {min_time}")
		print(f"max time: {max_time}")
		print(f"avg time: {avg_time}")

		print()
		print(f"best connection:")
		print(f"\033[1m{best_conn.summary}\033[0m")
		for step in best_conn.steps:
			print(f"\t{step}")

		print()
		print(f"worst connection:")
		print(f"\033[1m{worst_conn.summary}\033[0m")
		for step in worst_conn.steps:
			print(f"\t{step}")
