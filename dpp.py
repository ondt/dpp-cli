#!venv/bin/python
import sys
from core.web import DPP

dpp = DPP()

title, connections = dpp.query_connection(sys.argv[1], sys.argv[2])
