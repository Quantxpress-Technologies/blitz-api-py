# Libraries and SDKs

Below is a list of client libraries for BlitzConnect written in various programming languages. These libraries allow you to interact with the APIs without having to make raw HTTP calls.

| Language | Repository | Examples |
|----------|------------|----------|
| Python | [blitzsdk](https://pypi.org/project/blitzsdk/) | [Examples](https://github.com/example/blitzsdk/tree/main/examples) |
| C# (.NET 8) | [QX.BlitzConnect](https://github.com/example/QX.BlitzConnect) | [Examples](https://github.com/example/QX.BlitzConnect/tree/main/examples) |

=== "Python"

    ```bash
    pip install blitzsdk
    ```

    ```python
    from blitzsdk import InteractiveApiClient, MarketDataApiClient

    client = InteractiveApiClient(app_key="YOUR_KEY", user_id="YOUR_USER")
    md_client = MarketDataApiClient(app_key="YOUR_KEY", user_id="YOUR_USER")
    ```

=== "C#"

    Add project references to your `.csproj`:

    ```xml
    <ItemGroup>
      <ProjectReference Include="..\QX.BlitzConnect.Interactive\InteractiveSdk.csproj" />
      <ProjectReference Include="..\QX.BlitzConnect.MarketData\MarketDataSdk.csproj" />
    </ItemGroup>
    ```

    ```csharp
    using QX.BlitzConnect.Interactive;
    using QX.BlitzConnect.MarketData;
    using QX.BlitzConnect.Common;

    var config = new BlitzConfig { AppKey = "YOUR_KEY", UserId = "YOUR_USER" };
    var client = new BlitzInteractiveApiClient(config);
    await client.LoginAsync();

    var mdClient = new BlitzMarketDataApiClient(config);
    await mdClient.LoginAsync();
    ```

## Version and API endpoint

The current stable version of the API is **1**. All requests go to the base URLs listed in the [Introduction](index.md#base-urls).

### Root API endpoints

| Service | Endpoint |
|---------|----------|
| Authentication | `http://{host}/api_gateway/v1` |
| Interactive | `http://{host}/api_interactive/api/v1` |
| Market Data | `http://{host}/md-api` |
| Instruments | `http://{host}/v1/api` |
