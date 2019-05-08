import json
import math
import re
import time
from typing import List, Tuple
import cursor
import requests
from lxml import html

from core.models import Connection, RideStep, WalkStep



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

		try:
			cursor.hide()
			print(f"loading... 0% ", end="\r")

			while connections_received < num:
				if connections_received == 0:
					res = self.http.post("http://spojeni.dpp.cz/", form)  # the 1st request
				else:
					next_url = tree.cssselect("#ctlPaging_ctlPaging > a:contains('následující')")[0].attrib["href"]
					res = self.http.post(f"http://spojeni.dpp.cz/{next_url}")  # following requests

				assert "frmResult" in res.text, "unknown response received"

				tree = html.fromstring(res.content, parser=html.HTMLParser(encoding=res.encoding))  # the last one will remain
				connections_received = len(tree.cssselect(".spojeni"))  # todo: optimize
				print(f"loading... {round(connections_received / (math.ceil(num / 3) * 3) * 100)}% ", end="\r")

		finally:
			cursor.show()

		print(" " * 16, end="\r")  # cleanup

		# ---------------------------------------------------------------- #


		result = tree.cssselect("#frmResult")[0]

		title = result.cssselect("h1")[0].text
		connections: List[Connection] = []

		# for datetime, steps in zip(result.cssselect(".souhrn-spojeni .date"), result.cssselect(".spojeni")):
		for steps in result.cssselect(".spojeni"):
			connection = Connection()
			# connection.datetime = datetime.text

			for step in steps.getchildren():
				if step.tag == "h3":
					strong = list(step.cssselect("strong")[0].itertext())
					h3 = list(step.itertext())
					connection.summary = f"{strong[0].strip()} - {strong[-1].strip()}, {h3[-2].strip()} {h3[-1].strip()}"

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

						start_place, start_time = [x.strip() for x in start.rsplit(",", 1)]
						end_place, end_time = [x.strip() for x in end.rsplit(",", 1)]

						vehicle_type = vehicle.cssselect("a > img")[0].attrib["src"][4:-6]
						vehicle = "".join([x for x in vehicle.cssselect("a")[0].itertext() if x != "é"]).strip()

						connection.steps.append(RideStep(vehicle_type, vehicle, start_time, end_time, start_place, end_place))

					if step.attrib["class"] == "walk":
						connection.steps.append(WalkStep(text=step.text.strip().lower()))

					if step.attrib["class"] == "note":
						pass

				if step.tag == "div":
					pass

			connections.append(connection)

			if len(connections) >= num:
				break

		return title, connections
