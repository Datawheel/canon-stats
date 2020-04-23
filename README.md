# Canon-Stats: Library for Economic Complexity and Statistics calculations "on the fly"

Canon-stats is a node-js library, whose purpose is to simplify the labor of doing complex calculations in the front-end. It integrates with [@datawheel/canon-core](https://github.com/Datawheel/canon) and [tesseract-olap/tesseract](https://github.com/tesseract-olap/tesseract). Both are open source technologies developed and supported by Datawheel.

## Installation

The library will work only in repositories that it has installed `@datawheel/canon-core` previously.

```
npm i https://github.com/Datawheel/canon-stats
```

The environment variable `CANON_STATS_API` must be set, where the value is a tesseract instance URL.

```
export CANON_STATS_API=https://api.datamexico.org/tesseract
```

Once the package has been installed on any site using `@datawheel/canon-core`, the canon core server will automatically hook up the necessary cache and api routes for the stats endpoints.


## Python environment

Canon-stats requires that the server has previously installed python.

We suggest in local environment to create a virtual environment.
```
pip install virtualenv
virtualenv venv
source ./venv/bin/activate
pip install -r requirements.txt
```


## Usage

By default, stats exposes an endpoint at `/api/stats/<endpoint>` that will return JSON based on a series of query arguments. As simple example, using the Data México API, `api/stats/eci` returns ECI values for at state level:

```
/api/stats/eci?cube=inegi_economic_census&rca=State,Sector,Total Gross Production&Year=2014
```

```
{
  "data": [
    {
      "State": "Aguascalientes",
      "State ID": 1,
      "Total Gross Production ECI": -0.525816473
    },
    {
      "State": "Baja California",
      "State ID": 2,
      "Total Gross Production ECI": 0.0418928596
    },
    {
      "State": "Baja California Sur",
      "State ID": 3,
      "Total Gross Production ECI": 0.8143393184
    },
    ...
  ]
}
```

You can customize the endpoint URL, using the environment variable `CANON_STATS_BASE_URL`.

```
export CANON_STATS_BASE_URL=/api/mystats
```

The endpoint would be:
```
/api/mystats/eci?cube=inegi_economic_census&rca=State,Sector,Total Gross Production&Year=2014
```

Also, you can customize the endpoint URL for the POPULATION data, used for thresholding the results by country population. This it's done in the variable `CANON_STATS_POPULATION_BASE`.

```
export CANON_STATS_POPULATION_BASE="https://dev.oec.world/olap-proxy/data"
```

You need to add the params for the population data in the variable `CANON_STATS_POPULATION_PARAMS`, as it shows below

```
export CANON_STATS_POPULATION_PARAMS="Indicator:SP.POP.TOTL|drilldowns:Country|measures:Measure|cube:indicators_i_wdi_a"
```

Whit that done, the endpoint for population data would be:
```
https://dev.oec.world/olap-proxy/data/Indicator=SP.POP.TOTL&drilldowns=Country&measures=Measure&cube=indicators_i_wdi_a&Year=2014
```


## Endpoints availables

The stats module includes endpoints for doing different calculations. 

### Complexity

| variable | description |
| - | - |
| eci | Calculates Economic Complexity Index (Hidalgo & Haussmann, 2009) |
| rca | Calculates Balassa (1964) index |
| proximity |  |
| opportunity_gain |  |
| relatedness |  |


#### Query params

* options: Let's customize the output of the endpoint. 
* method: Value accepted: "subnational".

### Networks

Coming soon...


### Regressions

`OLS`

Regression tool based on statmodels.ols.
Requires at least two column of values.
Makes a regression on the first column, using as regresssors the data from the other columns.
Returns a JSON string with the following info:


| Summary | description |
| - | - |
| `Model` | Model used on the regression  |
| `Rsquared` | R-squared of the model  |
| `Adj. squared` | Adjusted R-squared  |
| `F-statistic` | 	F-statistic of the fully specified model  |
| `Log-Likelihood` | Log-likelihood of model  |
| `AIC` | 	Akaike’s information criteria  |
| `BIC` | 	Bayes’ information criteria.  |
| `No. Observations` | 	Number of observations n.  |


| Measures | description |
| - | - |
| `id` | Parameter estimate name  |
| `params` | Parameter estimate value  |
| `bse` | 	The standard errors of the parameter estimates.  |
| `t_values` | 	t-statistic for a given parameter estimate  |
| `p_values` | 	Two-tailed p values for the t-stats of the params  |
| `low_cof_int` | Lower bound of the confidence interval of the parameter estimate  |
| `upp_cof_int` | Upper bound of the confidence interval of the parameter estimate  |




`Arima`

Prediction tool based on statmodels.arima
Integrates a function to test some combination of values in order to find the best parameters (p,d,q) for the arima model.

Example of use and return:
```
api/stats/arima?cube=trade_s_jpn_m_hs&drilldowns=Month%2CSection&measures=Trade+Value&parents=true&sparse=false&Section=1,2
```
For the in-sample values doesn't return bounds
```
{
  "data": {
    "predictions": [
      {
        "Trade Value": 163507725000,
        "Trade Value Prediction": 776612778.6259537,
        "Trade Value Lower Bound": null,
        "Trade Value Upper Bound": null,
        "Section": "Animal Products",
        "Section ID": 1,
        "Date": "2009-01"
      },
```

For out-of-sample values returns also bounds from arima.forecast
```
 {
        "Trade Value": null,
        "Trade Value Prediction": 254371299939.10284,
        "Trade Value Lower Bound": 197551025677.41815,
        "Trade Value Upper Bound": 311191574200.78754,
        "Section": "Animal Products",
        "Section ID": 1,
        "Date": "2020-02"
      },
```
Model info
```
 "Model_info": [
      {
        "Section": "Animal Products",
        "args_used": [
          0,
          1,
          1
        ],
        "Model_info": "ARIMA",
        "Method": "css-mle",
        "No. Observations": 131,
        "AIC": 6691.658218470784,
        "BIC": 6700.283810440387,
        "HQIC": 6695.1631819518925
      },
```


`Prophet`

fbprophet Info
Uses fbprophet to make predictions for a time period.
fbprophet admits two columns estrictly named "ds" which stands for datestamp and "y" where all the values are stored.
Additional information can be found on the original paper: https://peerj.com/preprints/3190/
 

IMPORTANT!!! after a fbprophet update, a "cannot import easter from holidays" message appear, that is fixed installing holidays version 0.9.12

Example of use and return:
```
api/stats/prophet?cube=trade_s_jpn_m_hs&drilldowns=Month%2CSection&measures=Trade+Value&parents=true&sparse=false&Section=1,2
```
It is mandatory to have parents=true because of the 

In-sample return:
```
{
  "data": {
    "predictions": [
      {
        "Date": "2009-01",
        "Trade Value Prediction": 156206379624.48013,
        "Trade Value Lower Bound": 121951658678.74532,
        "Trade Value Upper Bound": 186771967062.42905,
        "Trade Value Trend": 162275525809.52594,
        "Trade Value Lower Trend": 162275525809.52594,
        "Trade Value Upper Trend": 162275525809.52594,
        "Section": "Animal Products",
        "Section ID": 1,
        "Trade Value": 163507725000
      },
```

Future Value
```
 {
        "Date": "2020-02",
        "Trade Value Prediction": 241277928164.69873,
        "Trade Value Lower Bound": 209091262304.9496,
        "Trade Value Upper Bound": 274741926365.10962,
        "Trade Value Trend": 253951981272.69458,
        "Trade Value Lower Trend": 253947746342.3182,
        "Trade Value Upper Trend": 253956814318.62085,
        "Section": "Animal Products",
        "Section ID": 1,
        "Trade Value": null
      },
```


The user is elegible to change parameters, also they are shown in the following JSON.
```
    "prophet_args": [
      {
        "seasonality_mode": "multiplicative"
      },
      {
        "changepoint_prior_scale": 0.05
      },
      {
        "changepoint_range": 0.95
      },
      {
        "periods": 10
      }
```
There is a range of values that each argument can have:

| Argument | Value |
| - | - |
| `seasonality_mode` | additive or multiplicative |
| `changepoint_prior_scale` | 0 < value < 1 |
| `changepoint_range` | 0 < value < 1|
| `periods` | any integer |