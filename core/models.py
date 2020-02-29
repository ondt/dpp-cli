from typing import List



class Step(object):
	pass



class WalkStep(Step):
	def __init__(self, text: str = ""):
		self.text = text

	def __str__(self):
		return self.text



class RideStep(Step):
	def __init__(self, vehicle_type: str = "", vehicle: str = "", start_time: str = "", end_time: str = "", start_place: str = "", end_place: str = ""):
		self.vehicle_type = vehicle_type
		self.vehicle = vehicle
		self.start_time = start_time
		self.end_time = end_time
		self.start_place = start_place
		self.end_place = end_place

	def __str__(self):
		color = ""
		if self.vehicle_type == "bus":
			color = "\033[34m"  # blue
		if self.vehicle_type == "train":
			color = "\033[34m"  # blue
		if self.vehicle_type == "tram":
			color = "\033[91m"  # red
		if self.vehicle_type == "metro":
			if "A" in self.vehicle:
				color = "\033[32m"  # green
			if "B" in self.vehicle:
				color = "\033[33m"  # yellow
			if "C" in self.vehicle:
				color = "\033[31m"  # red

		return f"{color}{self.vehicle:<14} {self.start_time:0>5} - {self.end_time:0>5}       {self.start_place} --> {self.end_place}\033[0m"  # todo zvyraznit start a end


class Connection(object):
	def __init__(self, time_from: int = None, time_to: int = None, transfers: int = None, duration: int = 0, steps: List[Step] = None):
		self.time_from = time_from
		self.time_to = time_to
		self.transfers = transfers
		self.duration = duration

		if steps is None: steps = []
		self.steps = steps


	def __str__(self):
		return f"{self.time_from} - {self.time_to}, {self.duration}"
