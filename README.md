# Canon-Stats: Library for Economic Complexity and Statistics Calculations "on the fly"

Canon-stats is a node-js library, whose purpose is to simplify the labor of doing complex calculations on the front-end. It integrates with [@datawheel/canon-core](https://github.com/Datawheel/canon) and [tesseract-olap/tesseract](https://github.com/tesseract-olap/tesseract). Both are open source technologies developed and supported by [Datawheel](https://datawheel.us).

This library creates REST-APIs in JSON format, that you can use on the front-end, and it is based on the integration of `python` calculations with `node`, and those calculations are encapsulated on `expressJS`.

## Installation

### Python environment

Canon-stats requires that the server has previously installed python (For more information about python installation, [click here](https://www.python.org/downloads/)).

IMPORTANT: We suggest to copy `requirements.txt` of this repository in the repository where you are working.

#### Install the libraries
##### Local environment

We suggest to create a virtual environment. You can use `virtualenv` for doing this task.
```
pip install virtualenv
virtualenv venv
source ./venv/bin/activate
pip install -r requirements.txt
```
##### Server environment
On the server, you need to run:

```
pip install -r /path/to/file/requirements.txt
```

Please make sure that each library has been installed successfully.

### Node environment

The library will work only in repositories that it has installed `@datawheel/canon-core` previously.

Since `canon-stats` is a private library, before to install for first time in a repository, it is required to include an authentication for a user called `datawheel-deploy`, who will drive the installation.

```
git config --global url."https://a164d0033398f6a1db0be16428b955e83b16b48b:x-oauth-basic@github.com/".insteadOf https://x-oauth-basic@github.com/
```
Now we can install the repository via `npm`
```
npm i https://github.com/Datawheel/canon-stats
```

Once the package has been installed on any site using `@datawheel/canon-core`, the canon core server will automatically hook up the necessary cache and api routes for the `canon-stats` endpoints.

### Update version installed

If you need to update the version installed on your repository, use:
```
npm update @datawheel/canon-stats
```

## Environment variables

Canon-stats requires a canon-cms specific env var for the current location of your  tesseract installation.
```
export CANON_STATS_API=https://tesseract-url.com/
```

For example, the env var used on DataMEXICO is:
```
export CANON_STATS_API=https://api.datamexico.org/tesseract
```
Other custom env vars for the library can be found on the table.
| env var | description | default  |
|---|---|---|
| `CANON_STATS_BASE_URL` | Customize the endpoint's URL | `/api/stats` |
| `CANON_STATS_TIMEOUT` | Sets the response timeout of a API | `undefined` |


## Endpoints availables

This library includes different statistical modules.

### [Complexity](docs/COMPLEXITY.md)
Based on Economic Complexity studies, this module calculates different metrics such as RCA, ECI, Proximity, Relatedness, Networks, among other metrics.

### [Regressions](docs/REGRESSIONS.md)
Allows to calculate Long-Short Term Models (LSTM) such as Prophet, and statistical models such as OLS, Logit.