# Canon-Stats: Library for Economic Complexity and Statistics Calculations "on the fly"

Canon-stats is a node-js library, whose purpose is to simplify the labor of doing complex calculations on the front-end. It integrates with [@datawheel/canon-core](https://github.com/Datawheel/canon) and [tesseract-olap/tesseract](https://github.com/tesseract-olap/tesseract). Both are open source technologies developed and supported by [Datawheel](https://datawheel.us).

This library creates REST-APIs in JSON format, and it is based on the integration of `python` calculations with `node`, and those calculations are encapsulated on `expressJS`.

## Installation

### 1) Python Environment

Canon-stats requires that the server has previously installed python (For more information about python installation, [click here](https://www.python.org/downloads/)).

**IMPORTANT**: We suggest to copy `requirements.txt` file in the repository where you are working.

#### Installing Python Libraries
##### Local Environment

We suggest to create a virtual environment. You can use `virtualenv` for doing this task.
```
pip install virtualenv
virtualenv venv
source ./venv/bin/activate
pip install -r requirements.txt
```
##### Server Environment
On the server, you need to run:

```
pip install -r /path/to/file/requirements.txt
```

Please make sure that each library has been installed successfully.

### 2) Node Environment

The library will only work in repositories that have `@datawheel/canon-core` pre-installed.

Since `canon-stats` is a private library, before to install it for the first time on a new project, it is required to include an authentication for a user called `datawheel-deploy`, who will drive the installation.

In the terminal of your laptop, execute this git command:
```
git config --global url."https://a164d0033398f6a1db0be16428b955e83b16b48b:x-oauth-basic@github.com/".insteadOf https://x-oauth-basic@github.com/
```
**IMPORTANT**: Please don't upload this command in a public repository, because it includes the authentication key associated to `datawheel-deploy`.

Now we can install the repository via `npm`
```
npm i https://github.com/Datawheel/canon-stats
```

Installing a specific version:
```
npm i https://github.com/Datawheel/canon-stats#0.6.1
```

Once the package has been installed on any site using `@datawheel/canon-core`, the canon core server will automatically hook up the necessary cache and api routes for the `canon-stats` endpoints.

**TIP**: If you need to update the version installed on your repository, use:
```
npm update @datawheel/canon-stats
```

## Environment Variables

Canon-stats requires a specific env var for the current location of your tesseract installation.
```
export CANON_STATS_API=https://tesseract-url.com/
```

For example, the env var used on DataMEXICO is:
```
export CANON_STATS_API=https://api.datamexico.org/tesseract
```
Optional env vars for the library are defined on the table.
| env var | description | default  |
|---|---|---|
| `CANON_STATS_BASE_URL` | Customize the endpoint's URL | `/api/stats` |
| `CANON_STATS_PYTHON_ENGINE` | Sets the python's engine used for running the library. | `python3` |
| `CANON_STATS_TIMEOUT` | Sets an API request timeout. | `undefined` |
| `OLAP_PROXY_SECRET` | Gets data from private cubes defined on tesseract. | `undefined` |


## Cache
This library includes a module that stores calculations used on Economic Complexity into a cache. This options currently works using `Redis` database.

Please make sure that `Redis` is running on your server before to use this module.

If you use linux:
```
sudo apt install redis-server
```

On your env vars, you will need to include
```
export CANON_STATS_CACHE="true"
export CANON_STATS_CACHE_URL="redis://[[username]:[password]]@localhost:6379/0"
```

For more information about URL used on `CANON_STATS_CACHE_URL`, [click here](https://redis-py.readthedocs.io/en/stable/#redis.ConnectionPool.from_url).

## Endpoints availables

This library includes different statistical modules.

### [Complexity](docs/COMPLEXITY.md)
Based on Economic Complexity studies, this module calculates different metrics such as RCA, ECI, Proximity, Relatedness, Networks, among other metrics.

### [Regressions](docs/REGRESSIONS.md)
Allows to calculate Long-Short Term Models (LSTM) such as Prophet, and statistical models such as OLS, Logit.