from typing import List


class Step(object):
	pass


class WalkStep(Step):
	pass


class RideStep(Step):
	pass


class Connection(object):
	datetime: str = ""
	summary: str = ""

	steps: List[Step] = []
