## Installation

```
npm i https://github.com/Datawheel/canon-stats
```

Also, the environment variable `CANON_STATS_API` must be set, where the value is a tesseract instance URL.

```
export CANON_STATS_API=https://api.datamexico.org/tesseract/
```

Once the package has been installed on any site using @datawheel/canon-core, the canon core server will automatically hook up the necessary cache and api routes for the stats endpoints.

### Python environment

```
pip3 install virtualenv
virtualenv venv
source ./venv/bin/activate
pip3 install -r requirements.txt
```


## Usage

By default, stats exposes an endpoint at `/api/stats/<endpoint>` that will return JSON based on a series of query arguments. As simple example, using the Data México cube, this endpoint would return ECI data for Mexico states:

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

Also, you can customize the endpoint URL, using the environment variable `CANON_STATS_BASE_URL`.

```
export CANON_STATS_BASE_URL=/api/customStats
```

The endpoint would be:
```
/api/customStats/eci?cube=inegi_economic_census&rca=State,Sector,Total Gross Production&Year=2014
```

## Endpoints availables

The stats module includes endpoints for doing different calculations. 

### Complexity

| variable | description | default |
| - | - | - |
| eci | Calculates Economic Complexity Index | |
| relatedness | Calculates Relatedness  |  |

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
Returns a JSON string with the following info:

| Model_info | description |
| - | - |
| `args_used` | Best (p,d,q) ARIMA parameters for the data   |
| `n_of_predictions` | User specified number of predictions  |
| `model_info` | Model used for the fitting  |
| `method` | Method used for loglikelihood  maximization.	  |
| `n_observations` | description  |
| `aic` | 	Akaike’s information criteria  |
| `bic` | 	Bayes’ information criteria.  |
| `hqic` | 	Hannan-Quinn information criterio  |
| `predictions` | Prediction results for the user specified number of predictions |

| params | description |
| - | - |
| `exog_name` | The names of the exogenous variable.  |
| `params` | Parameter estimate value  |
| `bse` | Standard errors of the parameter estimates  |
| `t_values` | t-statistic for a given parameter estimate  |
| `p_values` | The two-tailed p values for the t-stats of the params  |



`Prophet`

fbprophet Info
Uses fbprophet to make predictions for a time period.
fbprophet admits two columns estrictly named "ds" which stands for datestamp and "y" where all the values are stored.
Additional information can be found on the original paper: https://peerj.com/preprints/3190/

prophet.py breakdown
prophet.py admits time drilldowns such as "Year", "Month" and products drilldowns such as "Section".


```
prophet?cube=trade_i_baci_a_92&drilldowns=Year&measures=Trade+Value&parents=false&sparse=false
```
returns a JSON string with forecasted values and trend values, with their lower and upper bounds.

The user is elegible to change parameters, in particular those who are shown in the following table.

| variable | description | default | constraint |
| - | - | - | - |
| `changepoint_prior_scale` | Adjusts trend changes flexibility  | 0.05 | values between 0 and 1 |
| `changepoint_range` | Proportion of history in which trend changepoints will be estimated. | 0.95 | values between 0 and 1 |
| `periods` | Number of time periods used. | 10 | only natural numbers |
| `seasonality_mode` | the effect of the seasonality is added to the trend to get the forecast | multiplicative | only "additive" or "multiplicative " |

