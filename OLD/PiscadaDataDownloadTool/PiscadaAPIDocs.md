# History2 API

## Websocket vs. REST

History2 supports both REST and websocket. Cassandra Historian API only supports REST.

For websocket, connect to ws://localhost:3134, and send a json object with these parameters:
- *method* - [ *"GET"* | *"POST"* | *"PUT"* | *"DELETE"* ]
- *path* - The path part of the URL
- *params* - The query part of the URL

The result will be encapsulated in a json object:
- *status* - Corresponding HTTP result code
- *result* - The result (if successful)
- *error* - Error string (if error)


### Example

REST

```
GET http://localhost:3134/value/Utetemperatur?ts=2017-06-13T16:15
```

Websocket

```
{
    "method": "GET",
    "path": "/value/Utetemperatur",
    "params": {
        "from": "2017-06-13T16:15"
    }
}
```

Websocket result

```
{
    "result": 13.8,
    "status":200
}
```

## GET /value/*:tagname*
Return value of a tag at a given point in time

### Example

GET http://localhost:3134/value/Utetemperatur?ts=2017-06-13T16:15

```
13.8
```

## GET /timeseries/*:tagname*
Return raw timeseries for *:tagname*

### Parameters
- *from* - iso8601 timestamp.
- *to* - (optional) iso8601 timestamp. Defaults to current time.
- *time_format* - (optional) [ *'epoch'* | *'iso8601'* ]. Time format used in result. Set to 'epoch' to get ms since 1970-01-01 UTC. Defaults to 'iso8601'.

### Response
A json array of data points. Each datapoint is a json object:
- *ts* - Timestamp. String if *'time_format=iso8601'*, or milliseconds since 1970-01-01 UTC if *'time_format=epoch'*.
- *v* - Value. Decimal number.

The response will always include the last datapoint before, and the first datapoint after the given timerange, if these datapoints exists.

### Examples

GET http://localhost:3134/timeseries/Utetemperatur?from=2017-06-13T16:15

```
[
    { "ts":"2017-06-13T16:13:24.779", "v":13.8 },
    { "ts":"2017-06-13T16:15:42.866", "v":13.7 },
    { "ts":"2017-06-13T16:15:53.471", "v":13.8 },
    { "ts":"2017-06-13T16:16:31.715", "v":13.9 },
    { "ts":"2017-06-13T16:16:44.665", "v":13.8 },
    { "ts":"2017-06-13T16:17:24.400", "v":13.9 },
    { "ts":"2017-06-13T16:17:51.227", "v":14 },
    { "ts":"2017-06-13T16:17:52.873", "v":13.9 },
    { "ts":"2017-06-13T16:17:54.504", "v":14 },
    { "ts":"2017-06-13T16:19:01.062", "v":13.9 }
]
```

GET http://localhost:3134/timeseries/Utetemperatur?from=2017-06-13T16:15&to=2017-06-13T16:16

```
[
    { "ts":"2017-06-13T16:13:24.779", "v":13.8 },
    { "ts":"2017-06-13T16:15:42.866", "v":13.7 },
    { "ts":"2017-06-13T16:15:53.471", "v":13.8 },
    { "ts":"2017-06-13T16:16:31.715", "v":13.9 }
]
```

GET http://localhost:3134/timeseries/Utetemperatur?from=2017-06-13T16:15&to=2017-06-13T16:16&time_format=epoch

```
[
    { "ts":1497363204779, "v":13.8 },
    { "ts":1497363342866, "v":13.7 },
    { "ts":1497363353471, "v":13.8 },
    { "ts":1497363391715, "v":13.9 }
]
```

## GET /timeseries/aggregated/*:tagname*
Return aggregated timeseries for *:tagname*

### Parameters
- *from* - iso8601 timestamp.
- *to* - (optional) iso8601 timestamp. Defaults to current time.
- *time_format* - (optional) [ *'epoch'* | *'iso8601'* ]. Time format used in result. Set to 'epoch' to get ms since 1970-01-01 UTC. Defaults to 'iso8601'.
- *breakpoints* - (optional) [ *'true'* | *'false'* ]. Add breakpoints to all datapoints. Default is 'false'.
- *max_points* - (optional) Maximum number of datapoints returned. Not used if interval is given. Clamped to a value between 10 and 3000. Default is 300.
- *interval* - (optional) Time interval for aggregated datapoints. Format:
>1y - 1 year  
*n*M - *n* months, where *n* is 1,2,3,4 or 6.  
*n*w - *n* weeks, where *n* is 1,2,3,4,5,6,8 or 12.  
*n*d - *n* days, where *n* is 1,2,3,4,5 or 6.  
*n*h - *n* hours, where *n* is 1,2,3,4,6,8 or 12.  
*n*m - *n* minutes, where *n* is 1,2,3,4,5,6,10,12,15 or 20.  
*n*s - *n* seconds, where *n* is 1,2,3,4,5,6,10,12,15 or 20.

### Response
A json array of aggregated data points. Empty intervals are not returned.
- *ts* - Timestamp. Start time of datapoint. String if *'time_format=iso8601'*, or milliseconds since 1970-01-01 UTC if *'time_format=epoch'*.
- *avg* - Average value in time period. Decimal number.
- *min* - Number. Minimum value in time period.
- *max* - Number. Maximum value in time period.
- *interval* - (only returned in first datapoint) The time interval used for aggregation data.

The response will always include the last datapoint before, and the first datapoint after the given timerange, if these datapoints exists.

Breakpoints are added to aid plotting. Default is that breakpoints are added for datapoints far apart. If 'breakpoints=true' was specified, breakpoints are added for every datapoint. Extra datapoints are added for existing datapoints. The breakpoint has the same values as the datapoint, with the exception of *ts*, which is set equal to *ts* of the next datapoint.

If no *interval* is given, the smallest valid interval that divides the time period into less than *max_points* datapoints is used.

Aggregated data points will be aligned to the beginning of the year, month, week, day, etc.

### Examples

GET http://localhost:3134/timeseries/aggregated/Utetemperatur?from=2017-06-13T16:15&to=2017-06-13T16:20

```
[
    { "avg":13.8, "interval":"1s", "max":13.8, "min":13.8, "ts":"2017-06-13T16:13:24.000" },
    { "avg":13.8, "max":13.8, "min":13.8, "ts":"2017-06-13T16:13:25.000" },
    { "avg":13.8, "max":13.8, "min":13.8, "ts":"2017-06-13T16:13:25.000" },
    { "avg":13.8, "max":13.8, "min":13.8, "ts":"2017-06-13T16:15:42.000" },
    { "avg":13.7, "max":13.7, "min":13.7, "ts":"2017-06-13T16:15:42.000" },
    { "avg":13.7, "max":13.7, "min":13.7, "ts":"2017-06-13T16:15:43.000" },
    { "avg":13.7, "max":13.7, "min":13.7, "ts":"2017-06-13T16:15:43.000" },
    { "avg":13.8, "max":13.8, "min":13.8, "ts":"2017-06-13T16:15:53.000" },
    { "avg":13.8, "max":13.8, "min":13.8, "ts":"2017-06-13T16:15:54.000" },
    ...
    { "avg":13.9, "max":13.9, "min":13.9, "ts":"2017-06-13T16:19:25.000" },
    { "avg":13.9, "max":13.9, "min":13.9, "ts":"2017-06-13T16:19:26.000" },
    { "avg":13.9, "max":13.9, "min":13.9, "ts":"2017-06-13T16:19:26.000" },
    { "avg":14, "max":14, "min":14, "ts":"2017-06-13T16:21:47.000" }
]
```

GET http://localhost:3134/timeseries/aggregated/Utetemperatur?from=2017-06-13T16:15&to=2017-06-13T16:20&interval=5m

```
[
    { "avg":13.8, "interval":"5m", "max":13.8, "min":13.8, "ts":"2017-06-13T16:10:00.000" },
    { "avg":13.8, "max":13.8, "min":13.8, "ts":"2017-06-13T16:15:00.000" },
    { "avg":13.9, "max":14, "min":13.7, "ts":"2017-06-13T16:15:00.000" },
    { "avg":13.9, "max":14, "min":13.7, "ts":"2017-06-13T16:20:00.000" },
    { "avg":14, "max":14.1, "min":13.9, "ts":"2017-06-13T16:20:00.000" },
    { "avg":14, "max":14, "min":14, "ts":"2017-06-13T16:25:00.000" }
]
```

## GET /timeseries/aggregated (websocket only)
Get multiple tags in one query

### Parameters
- *tags* - A list of tags

Otherwise same as for *GET /timeseries/aggregated/:tagname*

### Response
Same as for *GET /timeseries/aggregated/:tagname*, but in a json array

### Example

```
{
    "method":"GET",
    "path":"/timeseries/aggregated",
    "params": {
        "tags": ["Innetemperatur", "Utetemperatur"],
        "from":"2017-06-13T16:10",
        "to":"2017-06-13T16:15",
        "interval":"5m"
    }
}
```

```
{
    "result": [
        [
            { "avg":23, "interval":"5m", "max":23, "min":23, "ts":"2017-06-13T16:05:00.000" },
            { "avg":23, "max":23, "min":23, "ts":"2017-06-13T16:10:00.000" },
            { "avg":23.06, "max":23.1, "min":23, "ts":"2017-06-13T16:10:00.000" },
            { "avg":23.06, "max":23.1, "min":23, "ts":"2017-06-13T16:15:00.000" },
            { "avg":23.12, "max":23.2, "min":23, "ts":"2017-06-13T16:15:00.000" },
            { "avg":23, "max":23, "min":23, "ts":"2017-06-13T16:20:00.000" }
        ],
        [
            { "avg":13.5, "interval":"5m", "max":13.5, "min":13.5, "ts":"2017-06-13T16:05:00.000" },
            { "avg":13.5, "max":13.5, "min":13.5, "ts":"2017-06-13T16:10:00.000" },
            { "avg":13.73, "max":13.8, "min":13.6, "ts":"2017-06-13T16:10:00.000" },
            { "avg":13.73, "max":13.8, "min":13.6, "ts":"2017-06-13T16:15:00.000" },
            { "avg":13.9, "max":14, "min":13.7, "ts":"2017-06-13T16:15:00.000" },
            { "avg":14, "max":14, "min":14, "ts":"2017-06-13T16:20:00.000" }
        ]
    ],
    "status":200
}
```

## POST /subscribe/servertime (websocket only)
Get controller's current time and timezone

### Example

```
{
    "method": "POST",
    "path": "/subscribe/servertime",
    "params": {
        "interval": "30m"
    }
}
```

```
{"result":true,"status":200}
```

And then, every half an hour:

```
{"current_time":"2017-06-26T20:30:00+02:00"}
```

## POST /subscribe/values (websocket only)
Subscribe for values as they come in

### Example

```
{
    "method": "POST",
    "path": "/subscribe/values",
    "params": {
        "tags": ["Innetemperatur", "Utetemperatur"]
    }
}
```

## Notes

All iso8601 datetime values are in the controller's timezone.
