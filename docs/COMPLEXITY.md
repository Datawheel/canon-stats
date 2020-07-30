# Complexity
As an academic field, Economic Complexity studies the geography and dynamics of economic activities using methods inspired in ideas from complex systems, networks, and computer science.

This module allows to calculate Economic Complexity measures. For further references about methodology and implicances of Economic Complexity itself, you can visit [oec.world](https://oec.world/en/resources/methods#economic-complexity).

## Endpoints

### ECI 
*GET* `/api/stats/eci`

Calculates Economic Complexity Index (ECI).

*returns* `<measure> ECI`

### Opportunity Gain 
*GET* `/api/stats/opportunity_gain`

### PCI
*GET* `/api/stats/pci`

Calculates Product Complexity Index (PCI).

*returns* `<measure> PCI`

### Proximity
*GET* `/api/stats/proximity`

### RCA
*GET* `/api/stats/rca`

Calculates Revealed Comparative Advantages (RCA).

*returns* `<measure> RCA`

### Relatedness
*GET* `/api/stats/relatedness`

Calculates Relatedness.

*returns* `<measure> Relatedness`

## Syntax

Complexity uses tesseract' logiclayer (LL) query parameters as reference. The simplest API requires to define two params: `cube` and `rca`. In the case of `rca`, the structure is: `<drilldown1>`, `<drilldown2>`, and `<measure>`. The first two params usually are a geo drilldown (country, regions, locations), a productive drilldown (industry/occupation/product); and measure is the value used for aggregations.
```
?cube=<cubeName>&rca=<drilldown1>,<drilldown2>,<measure>
```

IMPORTANT: You can use any `cut` based on LL format, like `&Year=2020`, `&Flow=1`, among others. Just remember those cuts must be valid drilldowns.

## Optional query params

### alias
Allows to use an `alias` for drilldowns. Sometimes, drilldown's name is different compared with the object returned by the API. For example, on OEC you use `rca=Exporter Country,HS4,Trade Value`, but the object returned by LL is `Country` instead of `Exporter Country`. In this case you must to use `alias=Country,HS4`. Syntax used is `alias=<alias_drilldown1>,<alias_drilldown2>`.

### eciThreshold
*Only valid for eci / pci endpoints*. Removes territories / products if they have less than N. Allows to remove noise before to calculate ECI / PCI.
```
&eciThreshold=Country:10,HS4:15
```

### filter_*
Filter results on a drilldown. This property requires the same name used on `rca`. If you defined `alias` on your query, you need to use those names.
```
&filter_Country=sachl&filter_HS4=10101
```

### method
Allows to calculate Economic Complexity measures, comparing the share of an activity in a local unit (e.g. region, province) with the share of that activity in the world. 
This is based on the methodology proposed on [oec.world](https://oec.world/en/resources/methods#uses). Values accepted are `subnational` and `relatedness`.


### iterations
Updates the number of iterations used for ECI / PCI calculations. Default value is `20`.

### options

Customize the output options of each endpoint. Currently, options are `limit` and `sort`.

* `limit`: Limits the number of elements returned by the endpoint.
* `sort`: Sorts data available according measure base of the URL. Accepted values are `desc` and `asc`.

For example, if you need the top-5 elements, you can use: 
```
options=limit:5,sort:desc
```

### ranking 
`(boolean)` Includes a ranking object based on the endpoint that you are using. E.g. `&ranking=true`. This ranking is done before to filter by a drilldown (see [filter_*](#filter_*))

### threshold
This options allows to remove noise from the data before to do calculations. You can do a threshold for any drilldown defined on `rca` param. Those thresholds are based on `measure`. If your queries uses `alias`, you will need to set up those drilldowns here.
```
threshold=Country:1000000,HS4:100
```

#### population threshold

In some case, you want to include a threshold by population.

You can customize the endpoint URL for the `POPULATION` data, used for thresholding the results by country population. This it's done in the env var `CANON_STATS_POPULATION_BASE`.

You will need to add the params for the population data in the variable `CANON_STATS_POPULATION_PARAMS`, as it shows below:

```
export CANON_STATS_POPULATION_BASE="https://oec.world/olap-proxy/data"
export CANON_STATS_POPULATION_PARAMS="Indicator:SP.POP.TOTL|drilldowns:Country|measures:Measure|cube:indicators_i_wdi_a"
```

With that done, the endpoint for population data would be:
```
threshold=Country:1000000,HS4:100,Population:1000000
```
## Examples

### 1) ECI of states in Mexico, using Economic Census cube and based on Total Gross Production

```
/api/stats/eci?cube=inegi_economic_census&rca=State,Industry Group,Total Gross Production&Year=2014
```

The endpoint will return the ECI for each `State` based on iterations using `Industry Group`, and the ECI will be named `Total Gross Production ECI`. Those values were calculated filtering by 2014.

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

* Balassa, B. (1965). Trade liberalization and revealed comparative advantage. _Manchester School of Economics and Social Studies_, 33, 99–123.
* Hidalgo, C. A., Klinger, B., Barabasi, A., &amp; Hausmann, R. (2007). The Product Space Conditions the Development of Nations. _Science_, 317(5837), 482-487. doi:10.1126/science.1144581
* Hidalgo, C. A., &amp; Hausmann, R. (2009). The building blocks of economic complexity. _Proceedings of the National Academy of Sciences_, 106(26), 10570-10575. doi:10.1073/pnas.0900943106
* Hidalgo, C. A., Balland, P., Boschma, R., Delgado, M., Feldman, M., Frenken, K., . . . Zhu, S. (2018). The Principle of Relatedness. _Unifying Themes in Complex Systems IX Springer Proceedings in Complexity_, 451-457. doi:10.1007/978-3-319-96661-8_46
* Catalán, P., Navarrete, C., &amp; Figueroa, F. (2020). The scientific and technological cross-space: Is technological diversification driven by scientific endogenous capacity? _Research Policy_, 104016. doi:10.1016/j.respol.2020.104016
