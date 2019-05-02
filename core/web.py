import json
import math
import re
import time
from typing import List, Tuple

import requests
from lxml import html

from core.models import Connection



class DPP(object):
	http = requests.session()
	asp_current_state = {}
	idoskey = ""

	def __init__(self):
		res = self.http.get("http://spojeni.dpp.cz/")
		self.remember_asp_state(res)  # save the asp tags
		self.idoskey = re.search("var sIDOSKey='(.*)';", res.text).group(1)  # save the idoskey  # var sIDOSKey='<key>';


	def remember_asp_state(self, res):
		tree = html.fromstring(res.content, parser=html.HTMLParser(encoding=res.encoding))

		for x in tree.cssselect('input[name^=__]'):  # all the asp tags
			self.asp_current_state[x.name] = x.value


	def autocomplete(self, query: str):
		headers = {
			"Content-Type": "application/json; charset=UTF-8",
			"idoskey":      self.idoskey,
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

		res = self.http.post("http://spojeni.dpp.cz/AJAXService.asmx/SearchTimetableObjects", data=json.dumps(body), headers=headers)

		results = json.loads(res.text)["d"]
		return [r["oItem"]["sName"] for r in results] if results else []


	def normalize(self, query: str):
		results = self.autocomplete(query)
		return results[0] if len(results) > 0 else query


	def query_connection(self, src: str, dst: str, via: str = "", num: int = 3) -> Tuple[str, List[Connection]]:
		src = self.normalize(src)
		dst = self.normalize(dst)

		form = {
			**self.asp_current_state,
			"ctlFrom$txtObject": src,
			"ctlTo$txtObject":   dst,
			"ctlVia$txtObject":  via,

			# "txtDate":           "1.5.2019",  # kdyz neni, tak se najde to nejaktualnejsi  # todo: arg
			# "txtTime":           "17:14",  # kdyz neni, tak se najde to nejaktualnejsi  # todo: arg

			"Direction":         "optDeparture",
			"Changes":           "optChanges",
			"cboChanges":        4,  # todo: arg
			"cmdSearch":         "vyhledat",
		}

		tree = None
		connections_received = 0
		est_conn_count = math.ceil(num / 3) * 3

		while connections_received < num:
			if connections_received == 0:
				res = self.http.post("http://spojeni.dpp.cz/", form)  # the 1st request
			else:
				next_url = tree.cssselect("#ctlPaging_ctlPaging > a:contains('následující')")[0].attrib["href"]
				res = self.http.post(f"http://spojeni.dpp.cz/{next_url}")  # following requests

			assert "frmResult" in res.text, "unknown response received"

			tree = html.fromstring(res.content, parser=html.HTMLParser(encoding=res.encoding))  # the last one will remain
			connections_received = len(tree.cssselect(".spojeni"))  # todo: optimize
			print(f"\rloading... {round(connections_received / est_conn_count * 100)}% ", end="")

		print("\r", " " * 15, end="\r")  # cleanup

		# ---------------------------------------------------------------- #


		result = tree.cssselect("#frmResult")[0]

		title = result.cssselect("h1")[0].text
		print(title)

		connections: List[Connection] = []

		for datetime, steps in zip(result.cssselect(".souhrn-spojeni .date"), result.cssselect(".spojeni")):
			connection = Connection()
			connection.datetime = datetime.text
			print()

			for step in steps.getchildren():
				if step.tag == "h3":
					strong = list(step.cssselect("strong")[0].itertext())
					h3 = list(step.itertext())
					connection.summary = f"{strong[0].strip()} - {strong[-1].strip()}, {h3[-1].strip()}"
					print(f"\033[1m{connection.summary}\033[0m")

				if step.tag == "p":
					if step.attrib["class"] == "usek":
						start, vehicle, end = step.getchildren()[:-1]

						# TODO: ?????????????
						if len(list(start.itertext())) == 4:
							start = "".join([list(start.itertext())[1], list(start.itertext())[3]]).strip()
						else:
							start = "".join(list(start.itertext())[1:]).strip()

						if len(list(end.itertext())) == 5:
							end = "".join([list(end.itertext())[1], list(end.itertext())[3]]).strip()
						else:
							end = "".join(list(end.itertext())[1:-1]).strip()

						# end = "".join(list(end.itertext())[1:-1]).strip()

						start, start_time = [x.strip() for x in start.rsplit(",", 1)]
						end, end_time = [x.strip() for x in end.rsplit(",", 1)]

						vehicle_type = vehicle.cssselect("a > img")[0].attrib["src"][4:-6]
						vehicle = "".join([x for x in vehicle.cssselect("a")[0].itertext() if x != "é"]).strip()

						# print(f"\t{vehicle} ({vehicle_type})")
						# print(f"\t\t{start} ({start_time}) --> {end} ({end_time})")

						if vehicle_type == "bus":
							print("\033[34m", end="")  # blue
						if vehicle_type == "train":
							print("\033[34m", end="")  # blue
						if vehicle_type == "tram":
							print("\033[91m", end="")  # red
						if vehicle_type == "metro":
							if "A" in vehicle:
								print("\033[32m", end="")  # green
							if "B" in vehicle:
								print("\033[33m", end="")  # yellow
							if "C" in vehicle:
								print("\033[31m", end="")  # red

						# print(f"\t{vehicle} ({vehicle_type})   \t {start_time} - {end_time}    \t {start} --> {end}")
						print(f"\t{vehicle:<14} {start_time:0>5} - {end_time:0>5}       {start} --> {end}")  # todo zvyraznit start a end

						print("\033[0m", end="")

					if step.attrib["class"] == "walk":
						print(f"\t{step.text.strip().lower()}")  # x minut na prestup

					if step.attrib["class"] == "note":
						pass

				if step.tag == "div":
					pass

			connections.append(connection)

			if len(connections) >= num:
				break

		return title, connections
