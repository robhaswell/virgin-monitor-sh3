# virgin-monitor-sh3
Monitor a Virgin SuperHub 3.0

This app is developed for personal use but I will offer limited assistance to others who wish to run it.

## Usage

Like any other python program, create a virtualenv, install the requirements and run `python app.py`.
Requires I think Python 3.6.

```sh
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
python app.py
```

App will run on http://127.0.0.1:8080

```
$ python app.py --help
usage: app.py [-h] [-c MY_CONFIG] [-p DB_PATH] [-i INTERVAL] [-u URL]

Args that start with '--' (eg. -p) can also be set in a config file
(~/.virgin-monitor or specified via -c). Config file syntax allows: key=value,
flag=true, stuff=[a,b,c] (for details, see syntax at https://goo.gl/R74nmi).
If an arg is specified in more than one place, then commandline values
override environment variables which override config file values which
override defaults.

optional arguments:
  -h, --help            show this help message and exit
  -c MY_CONFIG, --my-config MY_CONFIG
                        config file path
  -p DB_PATH, --db-path DB_PATH
                        database file path [env var: DB_PATH]
  -i INTERVAL, --interval INTERVAL
                        poll interval (seconds) [env var: POLL_INTERVAL]
  -u URL, --url URL     Endpoint URL [env var: URL]
  ```
