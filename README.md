## Installation

```
npm i https://github.com/Datawheel/canon-stats
```

Also, the environment variable `CANON_STATS_API` must be set, where the value is a tesseract instance URL.

```
export CANON_STATS_API=https://api.datamexico.org/tesseract/
```

Once the package has been installed on any site using @datawheel/canon-core, the canon core server will automatically hook up the necessary cache and api routes for the stats endpoints.




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
