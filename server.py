from argparse import ArgumentError

import eventlet.wsgi
import hug.api
from hug.middleware import CORSMiddleware

from core.web import DPP
from dpp import parser



hug_api = hug.API(__name__)
hug_api.http.add_middleware(CORSMiddleware(hug_api))  # disable CORS



@hug.get("/", output=hug.output_format.file)
def index():
	return "index.html"



@hug.get()
def connections(start: str, end: str, via: str = "", num: int = 3):
	dpp = DPP()

	try:
		title, conns = dpp.query_connection(from_stop=start, to_stop=end, via_stop=via, num=num)
	except AssertionError:
		title, conns = "No connections found", []

	return {
		"title":       title,
		"connections": dpp.connections_to_json(conns),
	}



@hug.get("/argparse/{args}")
def argparse(args: str):
	try:
		args = parser.parse_args(args.strip().split())
	except ArgumentError as e:
		return {
			"error": str(e)
		}
	except SystemExit:
		return {
			"help": parser.format_help(),
		}

	if not 0 < args.n <= 64:
		return {
			"error": "number must be in range: 0 < number <= 64"
		}

	# todo: format

	return {
		"args": {
			"start":  args.start,
			"end":    args.end,
			"via":    args.via if args.via else None,
			"num":    args.n,
			"format": args.f,
		},
		**connections(args.start, args.end, args.via, args.n),  # get the connections
	}



# start the server
eventlet.wsgi.server(eventlet.listen(addr=("localhost", 8001)), hug_api.http.server(), log_output=True)
# todo: https://fgimian.github.io/blog/2018/05/17/choosing-a-fast-python-api-framework/
