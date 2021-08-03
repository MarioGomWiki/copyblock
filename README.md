# copyblocks <!-- omit in toc -->

Copyblocks is a simple python script to automatically make global blocks based on blocks that any user has made locally on any WMF project.

- [Prerequistes](#prerequistes)
- [Setup](#setup)
- [Running the script](#running-the-script)
  - [Examples](#examples)
- [Performance](#performance)
- [Hacking](#hacking)

## Prerequistes

- bash- or bash-like shell environment
- functional installs of Python 3, pip and git


## Setup

Clone and enter this repository:

```shell
git clone https://github.com/MarioGomWiki/copyblock.git
cd copyblock
```

Install poetry and dependencies:

```shell
pip install poetry
poetry install
```

Create a `user-config.py` file with your wikimedia login credentials.

1. Visit [https://meta.wikimedia.org/wiki/Special:OAuthConsumerRegistration/propose](Special:OAuthConsumerRegistration/propose) and register OAuth credentials (tick "This consumer is for use only by [your username].")
2. In the copyblock folder, create an authentification file:

```shell
touch user-config.py
```

3. Enter the data for all wikis you want to use the script in. An example configuration that enables logging in on all WMF projects:

```python
usernames["*"]["*"] = "YourUser"
authenticate["*"] =  ('consumer_token', 'consumer_secret', 'access_token', 'access_secret')
```

4. Save and exit

## Running the script

```shell
$ poetry run ./copyblock.py --help
Usage: copyblock.py [OPTIONS]

Options:
  --lang TEXT               Language that the blocks should be imported from.
                            Default: "en"
  --site TEXT               Domain that the blocks should be imported from.
                            Default: "wikipedia"
  --dry-run / --really-run  Whether or not to actually execute the blocks or
                            make a dry run.  [required]
  --source-user TEXT        User whose blocks should be imported. Required
                            parameter.
  --ranges / --ips          Copy rangeblocks instead of IP blocks
  --comment-pattern TEXT    Regex to select only blocks containing certain
                            strings in the block summary. Default: Import all
                            blocks. Default: ".*".
  --verbose                 If specified, the script prints more verbose log
                            messages.
  --limit INTEGER           Maximum number of blocks to make. Default: No
                            limit.
  --block-reason TEXT       Block reason to use. Default: The existing local
                            block reason.
  --help                    Show this message and exit.
```

### Examples

Dry run: Get all blocks placed by ST47ProxyBot on enwiki that are still active, and contained the string "p2p" in the block summary, do not make any blocks, print verbose execution notes:

```shell
poetry run python copyblock.py --source-user ST47ProxyBot --comment-pattern p2p --verbose --dry-run
```

As above, but make a single test block with a custom reason:

```shell
poetry run python copyblock.py --source-user ST47ProxyBot --comment-pattern p2p --block-reason "[[m:NOP|Open proxy]]: Visit the [[m:NOP/P2P|help page]] if you are affected <!-- API-confirmed P2P proxy -->" --verbose --really-run --limit 1
```

Import all active blocks, without limiting to P2P blocks:

```shell
poetry run python copyblock.py --source-user ST47ProxyBot --block-reason "[[m:NOP|Open proxy]]: Visit the [[m:NOP/P2P|help page]] if you are affected <!-- API-confirmed P2P proxy -->" --verbose --really-run
```

## Performance

To maximize performance, you can disable all throttling limits, add to your `user-config.py`:

```python
# Maximum number of times to retry an API request before quitting.
max_retries = 0
# Minimum time to wait before resubmitting a failed API request.
retry_wait = 1
# Maximum time to wait before resubmitting a failed API request.
retry_max = 1

minthrottle = 0
maxthrottle = 0
put_throttle = 0
```

## Hacking

Did you modify the code? Please, run formatter, type check and test:

```shell
poetry run black .
poetry run mypy copyblock.py
poetry run pytest .
```
