# CDF hosted MQTT broker

Ingest live sensor datapoints into CDF data modeling time series through the CDF-hosted MQTT broker.

## What it does

Cognite hosts the MQTT broker and the extractor. You create four CDF resources — source, destination, mapping, and job — and publish Cognite-format JSON over MQTT. Datapoints land on data modeling `CogniteTimeSeries` instances identified by `(space, externalId)`.

```
mqtt_publisher.py
  │  publishes Cognite-format JSON over MQTT (TLS)
  ▼
CDF MQTT broker  ← Source (CDF hosts the broker)
  │
  │  Job subscribes to the topic and applies a Kuiper mapping
  ▼
CDF destination
  │
  └─► DM time series  instance_id = (mqtt_demo, mqtt_demo_ts_000000)
         auto-created on the first datapoint
```

| Resource        | Role                                                                 |
| --------------- | -------------------------------------------------------------------- |
| **Source**      | MQTT broker connection. CDF provisions it and returns credentials.   |
| **Destination** | Where the extractor writes data, authenticated with a session nonce. |
| **Mapping**     | Kuiper expression: MQTT JSON → CDF datapoint outputs.                |
| **Job**         | Links source → destination. Sets the topic filter and the mapping.   |

The notebook is safe to re-run: it updates those resources instead of duplicating them. The publisher simulates any number of series at a chosen rate. External IDs are `mqtt_demo_ts_000000` onward, in the `mqtt_demo` space.

## Prerequisites

- Python 3.14 or newer, and [uv](https://docs.astral.sh/uv/)
- A CDF project, and an identity with `hostedExtractors:READ` and `hostedExtractors:WRITE`

## How to use

1. Clone this repo and open it.
2. Install dependencies, including the notebook kernel:

   ```bash
   uv sync
   ```

3. Copy `.env.example` to `.env` and fill in your CDF project values. See [Configuration](#configuration).

   ```bash
   cp .env.example .env
   ```

4. Open `mqtt_demo/mqtt_extractor_setup.ipynb`, select the `.venv` kernel, and run all cells from the top through **Step 10**. Re-running is safe. The source cell writes `MQTT_HOST`, `MQTT_USERNAME`, and `MQTT_PASSWORD` into `.env`. The password is returned only when the source is created.
5. Publish simulated data from the repo root:

   ```bash
   uv run python mqtt_demo/mqtt_publisher.py 10 1hz
   uv run python mqtt_demo/mqtt_publisher.py 10 10hz
   uv run python mqtt_demo/mqtt_publisher.py 1000 1hz
   ```

   Frequency can be `1hz`, `0.5hz`, `10hz`, or an interval such as `2s`.

6. Confirm the pipeline, then stop the publisher with Ctrl-C when you are done.

   | Where                                        | What to look for                          |
   | -------------------------------------------- | ----------------------------------------- |
   | **Data management → Integrate → Extractors** | `mqtt_demo_source` — status **Connected** |
   | **Data → Time series** (space `mqtt_demo`)   | `mqtt_demo_ts_*` nodes updating live      |

   The notebook's monitor cell checks job status and throughput while the publisher is running.

7. Run the **Teardown** cell at the bottom of the notebook to delete the hosted extractor resources, the `mqtt_demo_ts_*` time series nodes, and the `mqtt_demo` space. Teardown removes the `MQTT_*` keys from `.env` and leaves the CDF login settings in place.

To write into a different space, change `SPACE` in `helpers/constants.py` before you run the notebook.

## Configuration

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

| Setting             | Where                  | Description                                                                                                    |
| ------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------- |
| `CDF_CLUSTER`       | `.env`                 | Cluster hostname prefix, for example `westeurope-1`. The client calls `https://<CDF_CLUSTER>.cognitedata.com`. |
| `CDF_PROJECT`       | `.env`                 | CDF project name.                                                                                              |
| `IDP_CLIENT_ID`     | `.env`                 | Entra ID app registration used to sign in.                                                                     |
| `IDP_TENANT_ID`     | `.env`                 | Entra ID tenant.                                                                                               |
| `IDP_CLIENT_SECRET` | `.env`                 | Required when `LOGIN_FLOW=client_credentials`.                                                                 |
| `LOGIN_FLOW`        | `.env`                 | `client_credentials` (default) or `interactive` for browser login.                                             |
| `MQTT_HOST`         | `.env`                 | Broker hostname. Written by the notebook when the source is created.                                           |
| `MQTT_PORT`         | `.env`                 | Broker port. Defaults to `8883`.                                                                               |
| `MQTT_USERNAME`     | `.env`                 | MQTT username generated by CDF.                                                                                |
| `MQTT_PASSWORD`     | `.env`                 | MQTT password generated by CDF. Returned only on first creation.                                               |
| `SPACE`             | `helpers/constants.py` | Data modeling space for the time series. Default `mqtt_demo`.                                                  |
| `MQTT_TOPIC`        | notebook, Step 2       | Topic the publisher uses and the job subscribes to. Default `cdf/data`.                                        |

`get_client()` reads `.env` once per kernel process. Restart the kernel after you edit `.env`.

## Known limitations

- The CDF-hosted MQTT broker source (`mqtt_broker`) is a beta API. The notebook calls it with `cdf-version: beta`. The Python SDK's MQTT source types are for a broker you host yourself, so they are not used here.
- The broker password is returned only when the source is created. If `.env` loses the `MQTT_*` keys, run Teardown and create the source again.
- Datapoints are written to data modeling time series only.
- The publisher uses QoS 0 and sends at most 1 000 time series per message, so a high-rate test does not queue payloads in memory.
