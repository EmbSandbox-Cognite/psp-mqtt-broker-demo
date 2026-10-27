"""CDF authentication helpers.

LOGIN_FLOW selects the OAuth flow:

    client_credentials   Service principal login (default).
    interactive          Browser login.
"""

from __future__ import annotations

import os
from pathlib import Path

from cognite.client import ClientConfig, CogniteClient
from cognite.client.credentials import OAuthClientCredentials, OAuthInteractive
from dotenv import load_dotenv

LOGIN_FLOWS = ("client_credentials", "interactive")


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"{name} is not set. Copy .env.example to .env and fill it in. "
            "If you just edited .env, restart the kernel — it is read once per process."
        )
    return value


def get_client(
    client_name: str = "mqtt-broker-demo",
    api_subversion: str | None = None,
) -> CogniteClient:
    """Build a CogniteClient from a .env file at the repo root.

    Required:
        CDF_CLUSTER, CDF_PROJECT, IDP_CLIENT_ID, IDP_TENANT_ID

    LOGIN_FLOW defaults to client_credentials, which also requires IDP_CLIENT_SECRET.
    Set LOGIN_FLOW=interactive for browser login.
    """
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")

    login_flow = os.environ.get("LOGIN_FLOW", "client_credentials").strip().lower()
    if login_flow not in LOGIN_FLOWS:
        raise ValueError(f"LOGIN_FLOW must be one of {LOGIN_FLOWS}, got {login_flow!r}")

    cluster = _require_env("CDF_CLUSTER")
    project = _require_env("CDF_PROJECT")
    client_id = _require_env("IDP_CLIENT_ID")
    tenant_id = _require_env("IDP_TENANT_ID")

    if login_flow == "client_credentials":
        credentials = OAuthClientCredentials.default_for_entra_id(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=_require_env("IDP_CLIENT_SECRET"),
            cdf_cluster=cluster,
        )
    else:
        credentials = OAuthInteractive.default_for_entra_id(
            tenant_id=tenant_id,
            client_id=client_id,
            cdf_cluster=cluster,
        )

    client = CogniteClient(
        ClientConfig(
            client_name=client_name,
            project=project,
            base_url=f"https://{cluster}.cognitedata.com",
            credentials=credentials,
            api_subversion=api_subversion,
        )
    )

    token = client.iam.token.inspect()
    print(f"Connected as : {token.subject}")
    print(f"Project      : {project}")
    print(f"Login flow   : {login_flow}")
    return client
