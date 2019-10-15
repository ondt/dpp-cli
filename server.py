import eventlet.wsgi
import hug.api
from hug.middleware import CORSMiddleware


hug_api = hug.API(__name__)
hug_api.http.add_middleware(CORSMiddleware(hug_api))  # disable CORS



@hug.get("/", output=hug.output_format.file)
def index():
	return "index.html"



@hug.get("/api/something")
def something():
	return {
		"some": "json",
	}



# start the server
# print(f"starting dpp server on {env.socketio_host}:{env.socketio_port}") # todo: argparse
eventlet.wsgi.server(eventlet.listen(addr=("localhost", 8001)), hug_api.http.server(), log_output=True)
# eventlet.wsgi.server(eventlet.listen(addr=("localhost", 8001)), __hug_wsgi__, log_output=True)
