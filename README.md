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

