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
	title, conns = dpp.query_connection(src=start, dst=end, via=via, num=num)

	return {
		"title":       title,
		"connections": dpp.render_conn2json(conns),
	}



@hug.get("/argparse/{args}")
def argparse(args: str):
	args = parser.parse_args(args.strip().split())

	# default n
	if args.n is None:
		args.n = 32 if args.stats else 3

	# todo: stats, format

	return {
		"args": {
			"start":  args.start,
			"end":    args.end,
			"via":    args.via,
			"num":    args.n,
			"format": args.f,
			"stats":  args.stats,
		},
		**connections(args.start, args.end, args.via, args.n),  # get the connections
	}



# start the server
eventlet.wsgi.server(eventlet.listen(addr=("localhost", 8001)), hug_api.http.server(), log_output=True)
