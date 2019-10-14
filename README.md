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

# cli...
python3 dpp.py malostranska krizikova

# ...or webserver
python3 server.py
```


## Usage
Malostranská - Křižíkova
```bash
python3 dpp.py malostranska krizikova
```
Křižíkova - Vyšehrad
```bash
python3 dpp.py kriz vyse
```
Webserver startup
```bash
python3 server.py
```


## Output
![output](https://i.imgur.com/AmlwSq5.png "output")
