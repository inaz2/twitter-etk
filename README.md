# Twitter ETK

Twitter ETK (Espionage Toolkit) is a tiny toolkit for finding some interesting information from Twitter.


## Installation

```
$ lsb_release -a
No LSB modules are available.
Distributor ID: Ubuntu
Description:    Ubuntu 12.04.3 LTS
Release:        12.04
Codename:       precise
```

```
$ sudo apt-get install python-virtualenv
$ sudo apt-get install build-essential python-dev
$ sudo apt-get install mongodb

$ cd twitter-etk
$ virtualenv ENV
$ source ENV/bin/activate
(ENV)$ pip install -r requirements.txt
```

## Preparation

You need to create your Twitter account and API keys.
Before using scripts, edit config.py and complete all keys.


## espionage.py

espionage.py is a script to retrieve and organize various data by using REST API.
This script runs without MongoDB.


## streamwatcher.py

streamwatcher.py is a script to watch filtered stream by using Streaming API.
This script runs without MongoDB.


## mongologger.py

mongologger.py is a script to collect tweets and analyze them by using Streaming API.
This script requires MongoDB on localhost.
