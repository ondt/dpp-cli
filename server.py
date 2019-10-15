import eventlet.wsgi
import hug.api
from hug.middleware import CORSMiddleware

from core.web import DPP


hug_api = hug.API(__name__)
hug_api.http.add_middleware(CORSMiddleware(hug_api))  # disable CORS



@hug.get("/", output=hug.output_format.file)
def index():
	return "index.html"



@hug.get()
def connections(start: str, end: str, via: str = "", num: int = 12):
	dpp = DPP()
	title, connections = dpp.query_connection(src=start, dst=end, via=via, num=num)

	return {
		"title":       title,
		"connections": dpp.render_conn2json(connections),
	}



# start the server
# print(f"starting dpp server on {env.socketio_host}:{env.socketio_port}") # todo: argparse
eventlet.wsgi.server(eventlet.listen(addr=("localhost", 8001)), hug_api.http.server(), log_output=True)
# eventlet.wsgi.server(eventlet.listen(addr=("localhost", 8001)), __hug_wsgi__, log_output=True)
