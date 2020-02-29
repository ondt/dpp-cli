# dpp-cli
dpp.cz command line interface



## Installation
```bash
sudo apt install git python3 python3-pip python3-venv  # python 3.6+, ideally
git clone https://github.com/ondt/dpp-cli
cd dpp-cli/

python3 -m venv venv
source venv/bin/activate  # posix shell
pip install -r requirements.txt
```



## Examples
Malostranská - Náměstí Míru
```bash
python3 dpp.py malo namesti_miru
```
Webserver startup
```bash
python3 server.py
```



## Usage
```
usage: dpp.py [-h] [-n NUMBER] [-f {pretty,json,pdf}] start [via] end

Find connections for Prague public transport.

positional arguments:
  start                 the starting station
  via                   via (optional)
  end                   the final station

optional arguments:
  -h, --help            show this help message and exit
  -n NUMBER             number of connections for search (default: 3)
  -f {pretty,json,pdf}  output format (default: pretty)
```




## Output
![output](https://i.imgur.com/AmlwSq5.png "output")
