# Complexity
This module allows to calculate different Economic Complexity measures.

## Endpoints

### ECI 
`/api/stats/eci`

### Opportunity Gain 
`/api/stats/opportunity_gain`

### PCI
`/api/stats/pci`

### Proximity
`/api/stats/proximity`

### RCA
`/api/stats/rca`

### Relatedness
`/api/stats/relatedness`

## Query structure

The simplest API needs: `cube` and `rca` params. In the case of `rca`, the structure is: `geo dimension`, `industry/product` dimension, and a `measure`.
```
?cube=<cubeName>&rca=<geo>,<product>,<measure>
```
All the tesseract logiclayer's params are valids, but it is required to use `rca` as param.

## Optional query params

### method
Allows to calculate Economic Complexity measures, comparing a subnational territory with the world, based on the methodology proposed on [oec.world](). Values accepted are `subnational` and `relatedness`.

### options
Customize the output options for each endpoint.

### Population threshold

In some case, you want to include a threshold by population.

You can customize the endpoint URL for the `POPULATION` data, used for thresholding the results by country population. This it's done in the variable `CANON_STATS_POPULATION_BASE`.

```
export CANON_STATS_POPULATION_BASE="https://dev.oec.world/olap-proxy/data"
```

You need to add the params for the population data in the variable `CANON_STATS_POPULATION_PARAMS`, as it shows below:

```
export CANON_STATS_POPULATION_PARAMS="Indicator:SP.POP.TOTL|drilldowns:Country|measures:Measure|cube:indicators_i_wdi_a"
```

With that done, the endpoint for population data would be:
```

```
## Examples

### 1) ECI of states in México

URL example
```
/api/stats/eci?cube=inegi_economic_census&rca=State,Sector,Total Gross Production
```

The endpoint will return the complexity value for each `State` based on iterations using `Sector`, and the ECI will be named `Total Gross Production ECI`.

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

### 2) Relatedness 

### 3) RCA subnational 




## References

* 
* Hidalgo, C. A., Klinger, B., Barabasi, A., &amp; Hausmann, R. (2007). The Product Space Conditions the Development of Nations. _Science_, 317(5837), 482-487. doi:10.1126/science.1144581
* Hidalgo, C. A., &amp; Hausmann, R. (2009). The building blocks of economic complexity. _Proceedings of the National Academy of Sciences_, 106(26), 10570-10575. doi:10.1073/pnas.0900943106
* Hidalgo, C. A., Balland, P., Boschma, R., Delgado, M., Feldman, M., Frenken, K., . . . Zhu, S. (2018). The Principle of Relatedness. _Unifying Themes in Complex Systems IX Springer Proceedings in Complexity_, 451-457. doi:10.1007/978-3-319-96661-8_46
* Catalán, P., Navarrete, C., &amp; Figueroa, F. (2020). The scientific and technological cross-space: Is technological diversification driven by scientific endogenous capacity? _Research Policy_, 104016. doi:10.1016/j.respol.2020.104016
