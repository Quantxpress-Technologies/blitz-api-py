# Signals

Send trading or strategy signals from a source strategy to destination strategies within the platform.

```
POST /signals
```

```bash
curl -X POST "http://uat.bull8.ai:7443/api_interactive/api/v1/signals" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {
        "SourceStrategy": "MyStrategy",
        "DestinationStrategy": "TargetStrategy",
        "SourceSID": "inst_001",
        "InstanceRunningMode": "Started",
        "GlobalAction": "Signal",
        "Instruments": [
            {
                "ExchangeSegment": "NSEFO",
                "InstrumentName": "NIFTY26FEB2625500PE",
                "Action": "BUY",
                "Lot": "1",
                "TimeStamp": "06-07-2026 09:15:00",
                "InfoText": "Entry Signal"
            }
        ]
    }
]'
```

## Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `SourceStrategy` | string | Name of the source strategy |
| `DestinationStrategy` | string | Name of the destination strategy |
| `SourceSID` | string | Strategy instance identifier |
| `InstanceRunningMode` | string | `Started` or `Stopped` |
| `GlobalAction` | string | `Signal`, `Exit`, etc. |
| `Instruments` | array | List of instrument actions |
| `ExchangeSegment` | string | `NSEFO`, `NSECM`, etc. |
| `InstrumentName` | string | Instrument symbol |
| `Action` | string | `BUY`, `SELL`, `EXIT` |
| `Lot` | string | Quantity in lots |
| `TimeStamp` | string | `dd-mm-yyyy HH:MM:SS` format |
| `InfoText` | string | Optional description |

## SDK

=== "Python"

    ```python
    signals = [{
        "SourceStrategy": "MyStrategy",
        "DestinationStrategy": "TargetStrategy",
        "SourceSID": "inst_001",
        "InstanceRunningMode": "Started",
        "GlobalAction": "Signal",
        "Instruments": [{
            "ExchangeSegment": "NSEFO",
            "InstrumentName": "NIFTY26FEB2625500PE",
            "Action": "BUY",
            "Lot": "1",
            "TimeStamp": "06-07-2026 09:15:00",
            "InfoText": "Entry Signal"
        }]
    }]
    result = client.send_signals(signals)
    ```

=== "C#"

    ```csharp
    var signals = new List<SignalRequest>
    {
        new SignalRequest
        {
            SourceStrategy = "MyStrategy",
            DestinationStrategy = "TargetStrategy",
            SourceSID = "inst_001",
            InstanceRunningMode = "Started",
            GlobalAction = "Signal",
            Instruments = new List<SignalInstrument>
            {
                new SignalInstrument
                {
                    ExchangeSegment = "NSEFO",
                    InstrumentName = "NIFTY26FEB2625500PE",
                    Action = "BUY",
                    Lot = "1",
                    TimeStamp = "06-07-2026 09:15:00",
                    InfoText = "Entry Signal"
                }
            }
        }
    };
    var result = await client.SendSignalsAsync(signals);
    ```
