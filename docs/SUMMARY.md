
# Summary

## Endpoints

### Rolling mean
- *BASE* `/api/stats/rolling`
- *returns* `<measure> Rolling Mean`

Rolling Mean uses different types of parameters. The first group is made up of mandatory parameters, among them are `cube`, `drilldowns` and `measure` that come from Tesseract, in the case of `drilldowns` there are two options:

1) `&drilldowns:<drilldowns1>,<drilldons2>`
  In this case, one of the two breakdowns must consider the geographical dimension and the other the time dimension, in the event that a time dimension less than Years is used, the following must be included: `&parents=true`

2) `&drilldowns:<drilldowns1>`
  In this case, the drilldowns must consider a time dimension, in the event that a time dimension less than Years is used, the following must be included: `&parents=true`

*Note:* In addition to this, the different cuts available in Tesseract can be incorporated.

On the other hand, there are the following optional parameters:

1) `&prediction=<value>`
  "true" is used when you want to obtain the rolling period of an additional period to the one available in the data.
  *defaul:* "false"

2) `&window=<value>`
  Number of observations used to calculate the statistic
  *defaul:* 3

3) `&periods=<value>`
  Minimum number of observations required to calculate the statistic of a window
  *defaul:* the value determined in the window

## Examples  

### 1) Only dimension time 

```
/api/stats/rolling?cube=trade_s_zaf_m_hs&drilldowns=Year&measures=Trade+Value&window=4&prediction=true&debug=true
``` 

The endpoint will return Rolling Mean for each year considering windows of 4 observations, additionally the value of the statistic is obtained for a year in the future (2021).

```
{
    data: [
        {
        Year: 2014,
        Trade Value: 2057971126788,
        Trade Value Rolling Mean: 1581144152100.5
        },
        ...
        {
        Year: 2020,
        Trade Value: 937754358940,
        Trade Value Rolling Mean: 2343303234938
        },
        {
        Year: 2021,
        Trade Value: 0,
        Trade Value Rolling Mean: 2035516449074.5
        }
    ]
}
```

```
/api/stats/rolling?cube=trade_s_zaf_m_hs&drilldowns=Month&measures=Trade+Value&window=4&periods=1&prediction=false&debug=true&parents=true
```
The endpoint will return Rolling Mean for each month considering windows of 4 observations, but since periods=1 in the first 3 observations the average will calculated only between the existing ones.

```
{
    data: [
        {
        Year: 2010,
        Month ID: 1,
        Quarter ID: 1,
        Quarter: "Q1",
        Month: "January",
        Trade Value: 82886859579,
        Trade Value Rolling Mean: 82886859579
        },
        {
        Year: 2010,
        Month ID: 2,
        Quarter ID: 1,
        Quarter: "Q1",
        Month: "February",
        Trade Value: 92906899018,
        Trade Value Rolling Mean: 87896879298.5
        },
        {
        Year: 2010,
        Month ID: 3,
        Quarter ID: 1,
        Quarter: "Q1",
        Month: "March",
        Trade Value: 108633356357,
        Trade Value Rolling Mean: 94809038318
        },
        ...
    ]
}
```

### 2) Two dimensions

```
/api/stats/rolling?cube=trade_s_esp_m_hs&drilldowns=Subnat+Geography,Year&measures=Trade+Value&parents=false&sparse=false
```
The endpoint will return the calculation of the rolling mean by geographic zones in each year considering windows of 3 observations and a minimum period similar to these, without predictions.

```
{
  data: [
    {
    Year: 2012,
    Subnat Geography ID: 1,
    Trade Value: 7935113630.254646,
    Trade Value Rolling Mean: 7569884615.168799,
    Subnat Geography: "Alava"
    },
    {
    Year: 2013,
    Subnat Geography ID: 1,
    Trade Value: 7737667357.976483,
    Trade Value Rolling Mean: 7893170718.35331,
    Subnat Geography: "Alava"
    },
    {
    Year: 2014,
    Subnat Geography ID: 1,
    Trade Value: 8192147353.564777,
    Trade Value Rolling Mean: 7954976113.931969,
    Subnat Geography: "Alava"
    },
    {
    Year: 2015,
    Subnat Geography ID: 1,
    Trade Value: 9133127050.807846,
    Trade Value Rolling Mean: 8354313920.783035,
    Subnat Geography: "Alava"
    },
    ...
  ]
}
```