## Usage


### Complexity

| variable | description |
| - | - |
| eci | Calculates Economic Complexity Index (Hidalgo & Haussmann, 2009) |
| rca | Calculates Balassa (1964) index |
| proximity |  |
| opportunity_gain |  |
| relatedness |  |


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

https://dev.oec.world/olap-proxy/data/Indicator=SP.POP.TOTL&drilldowns=Country&measures=Measure&cube=indicators_i_wdi_a&Year=2014

#### Query params

* options: Let's customize the output of the endpoint. 
* method: Value accepted: "subnational".
