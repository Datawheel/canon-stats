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