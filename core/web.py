import json
import math
import re
import time
from typing import List, Tuple

import cursor
import requests
from lxml import html

from core.models import Connection, RideStep, WalkStep



class DPP:
	http = requests.session()
	asp_current_state = {}
	idoskey = ""


	def __init__(self):
		res = self.http.get("https://spojeni.dpp.cz/")
		self.remember_asp_state(res)  # save the asp tags
		self.idoskey = re.search("var sIDOSKey='(.*)';", res.text).group(1)  # save the idoskey  # var sIDOSKey='<key>';



	def remember_asp_state(self, res):
		tree = html.fromstring(res.content, parser=html.HTMLParser(encoding=res.encoding))  # todo: optimize

		for x in tree.cssselect('input[name^=__]'):  # all the asp tags
			self.asp_current_state[x.name] = x.value



	def autocomplete(self, query: str):
		headers = {
			"idoskey": self.idoskey,
		}

		body = {
			"timestamp":        str(round(time.time() * 1000)),
			"prefixText":       query,
			"count":            "20",
			"selectedTT":       "PID",
			"bindElementValue": "",
			"iLang":            "CZECH",
			"bCoor":            "false",
			"iTrCatSelected":   "",
		}

		res = self.http.post("https://spojeni.dpp.cz/AJAXService.asmx/SearchTimetableObjects", json=body, headers=headers)

		results = res.json()["d"]
		return [r["oItem"]["sName"] for r in results] if results else []



	def autocomplete_alt(self, query: str):
		params = {
			"q":                f"\"{query}\"",
			"limit":            "20",
			"timestamp":        str(round(time.time() * 1000)),
			"selectedTT":       "\"PID\"",
			"bindElementValue": "",
			"iLang":            "\"CZECH\"",
			"bCoor":            "false",  # gives some coordinates
			"format":           "json",
		}

		res = self.http.get("https://spojeni.dpp.cz/AJAXService.asmx/SearchTimetableObjectsJSONP", params=params)

		results = json.loads(res.text[1:-2])["d"]  # (<content>);
		return [r["oItem"]["sName"] for r in results] if results else []



	def normalize(self, query: str):
		if not query: return ""
		results = self.autocomplete(query.replace("_", " "))
		return results[0] if len(results) > 0 else query  # todo: exception



	def query_connection(self, from_stop: str, to_stop: str, via_stop: str = "", num: int = 3, show_progress: bool = False) -> Tuple[str, List[Connection]]:
		from_stop = self.normalize(from_stop)
		to_stop = self.normalize(to_stop)
		via_stop = self.normalize(via_stop)

		tree = self._get_connections_page_tree(from_stop, to_stop, via_stop, num, show_progress)
		connections = self._parse_connections(tree)

		title = f"Spojení: {from_stop} - {to_stop}{'' if not via_stop else f' přes {via_stop}'}"
		return title, connections[:num]



	def pdf(self, from_stop: str, to_stop: str, via_stop: str = "", num: int = 3, show_progress: bool = False) -> bytes:
		from_stop = self.normalize(from_stop)
		to_stop = self.normalize(to_stop)
		via_stop = self.normalize(via_stop)

		tree = self._get_connections_page_tree(from_stop, to_stop, via_stop, num, show_progress)

		pdf_button = tree.cssselect("form")[1]  # second form tag
		next_url = pdf_button.attrib["action"]
		res = self.http.post(f"http://spojeni.dpp.cz/{next_url}")

		return res.content



	def _get_connections_page_tree(self, from_stop: str, to_stop: str, via_stop: str = "", num: int = 3, show_progress: bool = False) -> html.HtmlElement:
		form = {
			**self.asp_current_state,
			"ctlFrom$txtObject":     from_stop,
			"ctlVia$txtObject":      via_stop,
			"ctlTo$txtObject":       to_stop,

			"ctlFrom$txtSearchMode": "0",
			"ctlVia$txtSearchMode":  "0",
			"ctlTo$txtSearchMode":   "0",

			# "txtDate":                     "29.02.2020",
			# "txtTime":                     "12:30",

			"Direction":             "optDeparture",
			"cmdSearch":             "",
		}
		tree = None
		connections_received = 0
		try:
			cursor.hide()
			if show_progress: print(f"loading... 0% ", end="\r")

			while connections_received < num:
				if connections_received == 0:
					res = self.http.post("https://spojeni.dpp.cz/", form)  # the 1st request
				else:
					button = tree.cssselect("#ctlButtons a[title='zobrazit následující spoje']")  # no následující for the next day
					if not button:
						break

					next_url = button[0].attrib["href"]
					res = self.http.post(f"http://spojeni.dpp.cz/{next_url}")  # the chained requests

				assert "Vyskytl se problém" not in res.text
				assert "frmResult" in res.text, "Unknown response received."

				tree = html.fromstring(res.content, parser=html.HTMLParser(encoding=res.encoding))  # the last one will remain
				connections_received = len(tree.cssselect(".spojeni"))
				if show_progress: print(f"loading... {round(connections_received / (math.ceil(num / 3) * 3) * 100)}% ", end="\r")

		finally:
			cursor.show()

		if show_progress: print(" " * 16, end="\r")  # cleanup

		return tree



	@staticmethod
	def _parse_connections(tree: html.HtmlElement) -> List[Connection]:
		result = tree.cssselect("#frmResult")[0]
		connections: List[Connection] = []

		for conn_box in result.cssselect(".spojeni"):
			connection = Connection()

			trip_time = conn_box.cssselect(".LineTrack-tripTime")[0].text_content().strip()
			connection.time_from, connection.time_to = trip_time.split("–")
			connection.duration = conn_box.cssselect("strong")[1].text_content().strip()  # the second strong

			steps_tbody = conn_box.cssselect("table.LineTrack-connections > tbody")[0]
			for table_row in steps_tbody.getchildren():
				if len(table_row) == 0:
					continue

				vehicle_element, substeps = table_row

				assert len(substeps) in {1, 2}

				if len(substeps) == 1:  # ul (RideStep)
					ul = substeps.cssselect("ul")[0]
					li = ul.getchildren()

					things = []
					for item in li:
						stop_time = item.cssselect(".LineTrack-stopTime")[0].text_content().strip()
						stop_info = item.cssselect(".LineTrack-stopInfo")[0].text_content().strip()

						for a in stop_time.split():
							things.append((a, stop_info))

					assert len(things) % 2 == 0  # even
					things = iter(things)

					for index, x in enumerate(things):
						# parse the vehicle
						vehicle_type = vehicle_element.cssselect("svg > use")[index].attrib["xlink:href"].split("-")[-2]
						vehicle = vehicle_element.cssselect("strong")[index].text_content().strip()

						y = next(things)
						connection.steps.append(RideStep(
							vehicle_type=vehicle_type,
							vehicle_line=vehicle,
							start_time=x[0],
							end_time=y[0],
							start_place=x[1],
							end_place=y[1],
						))


				else:  # div, div (WalkStep)
					text = substeps.cssselect("i")[0].text_content().strip().lower()
					connection.steps.append(WalkStep(text))

			connections.append(connection)

		return connections



	@staticmethod
	def connections_to_str(connections: List[Connection]):
		output = []
		for connection in connections:
			output.append(f"\033[1m{connection}\033[0m\n")

			for step in connection.steps:
				output.append(f"\t{step}\n")

			output.append("\n")

		return "".join(output)



	@staticmethod
	def connections_to_json(connections: List[Connection]) -> List[dict]:
		return [
			{
				"time_from": c.time_from,
				"time_to":   c.time_to,
				"duration":  c.duration,
				"steps":     [
					{
						"type":        "ride",
						"vehicle":     {
							"type": s.vehicle_type,
							"line": s.vehicle_line,
						},
						"start_time":  s.start_time,
						"start_place": s.start_place,
						"end_time":    s.end_time,
						"end_place":   s.end_place,
					}
					if isinstance(s, RideStep) else
					{
						"type": "walk",
						"text": s.text,
					}
					for s in c.steps
				]

			} for c in connections
		]
