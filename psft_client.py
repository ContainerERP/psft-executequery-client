"""
psft_client.py – tiny helper for PeopleSoft ExecuteQuery REST calls.

Usage pattern:

    from psft_client import PeopleSoftClient, parse_executequery_xml

    client = PeopleSoftClient(
        base_url="https://192.168.232.228/PSIGW/RESTListeningConnector/PSFT_EP/ExecuteQuery.v1",
        auth=("PSREST", "your_password_here"),  # or ps_token="..."
        verify=False,   # DEV ONLY – skip SSL validation (like "Not secure → Proceed")
    )

    xml_text = client.execute_query(
        query_name="FM_VENDOR_MASTER",
        prompts={"VENDOR_STATUS": "I", "VENDOR_ID_OFFSET": ""},
        maxrows=10,
    )

    rows = parse_executequery_xml(xml_text)
    print(rows[0])

"""

from typing import Dict, List, Optional, Tuple, Union
import requests


AuthType = Optional[Tuple[str, str]]


class PeopleSoftClient:
    """
    Simple client for PeopleSoft ExecuteQuery.v1 endpoints.

    base_url should go up to *ExecuteQuery.v1*, e.g.:

        https://<host-or-ip>/PSIGW/RESTListeningConnector/PSFT_EP/ExecuteQuery.v1
    """

    def __init__(
        self,
        base_url: str,
        auth: AuthType = None,       # ("PSREST", "password") for Basic Auth
        ps_token: Optional[str] = None,  # PS_TOKEN cookie if you use PIA login
        verify: Union[bool, str] = True, # False or path to CA bundle
        timeout: int = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.ps_token = ps_token
        self.verify = verify
        self.timeout = timeout

    # -------------------- public API -------------------- #

    def execute_query(
        self,
        query_name: str,
        prompts: Dict[str, str],
        maxrows: int = 1000,
        isconnectedquery: str = "N",
        security: str = "public",
        output_path: str = "XMLP/NONFILE",
    ) -> str:
        """
        Call ExecuteQuery and return raw XML text.

        prompts: dict of {prompt_name: value}. Order is preserved in Python 3.7+.
                 Order matters because PeopleSoft expects names and values
                 aligned: prompt_uniquepromptname=A,B  prompt_fieldvalue=1,2
        """
        url = self._build_executequery_url(
            query_name=query_name,
            prompts=prompts,
            maxrows=maxrows,
            isconnectedquery=isconnectedquery,
            security=security,
            output_path=output_path,
        )
        cookies = {}
        if self.ps_token:
            cookies["PS_TOKEN"] = self.ps_token

        resp = requests.get(
            url,
            auth=self.auth,
            cookies=cookies,
            verify=self.verify,
            timeout=self.timeout,
        )
        # Raise a nice error if HTTP != 2xx
        try:
            resp.raise_for_status()
        except Exception as e:
            # Attach response text for easier debugging
            raise RuntimeError(
                f"PeopleSoft ExecuteQuery call failed: {resp.status_code}\n{resp.text}"
            ) from e

        return resp.text

    # -------------------- internal helpers -------------------- #

    def _build_executequery_url(
        self,
        query_name: str,
        prompts: Dict[str, str],
        maxrows: int,
        isconnectedquery: str,
        security: str,
        output_path: str,
    ) -> str:
        """
        Build a URL like:

        https://host/.../ExecuteQuery.v1/public/FM_VENDOR_MASTER/XMLP/NONFILE
          ?isconnectedquery=N
          &maxrows=1000
          &prompt_uniquepromptname=VENDOR_STATUS,VENDOR_ID_OFFSET
          &prompt_fieldvalue=I,
        """
        # Path part
        path = f"{self.base_url}/{security}/{query_name}/{output_path}".rstrip("/")

        # Important: keep commas *unencoded* for PeopleSoft
        prompt_names = ",".join(prompts.keys())
        prompt_values = ",".join((prompts[k] or "") for k in prompts.keys())

        query_str = (
            f"isconnectedquery={isconnectedquery}"
            f"&maxrows={maxrows}"
            f"&prompt_uniquepromptname={prompt_names}"
            f"&prompt_fieldvalue={prompt_values}"
        )

        return f"{path}?{query_str}"


# -------------------- XML parsing helper (optional) -------------------- #

import xml.etree.ElementTree as ET


def parse_executequery_xml(xml_text: str) -> List[Dict[str, str]]:
    """
    Parse PeopleSoft ExecuteQuery XML (like your FM_VENDOR_MASTER output)
    into a list of dicts, one per <row>.

    Each dict is {FIELDNAME: "value"}.

    This is namespace-agnostic and should work across environments.
    """
    root = ET.fromstring(xml_text)

    def strip_ns(tag: str) -> str:
        return tag.split("}", 1)[1] if "}" in tag else tag

    rows: List[Dict[str, str]] = []
    for node in root.iter():
        if strip_ns(node.tag) == "row":
            row_dict: Dict[str, str] = {}
            for child in list(node):
                field_name = strip_ns(child.tag)
                value = (child.text or "").strip()
                row_dict[field_name] = value
            rows.append(row_dict)

    return rows


# -------------------- quick CLI test -------------------- #

if __name__ == "__main__":
    # Example: adjust these for your env
    client = PeopleSoftClient(
        base_url="https://192.168.232.228/PSIGW/RESTListeningConnector/PSFT_EP/ExecuteQuery.v1",
        auth=("PSREST", "your_password_here"),
        verify=False,  # DEV ONLY – like clicking "Not secure → Proceed" in browser
    )

    # Prompts must match your Query's prompts and order
    prompts = {
        "VENDOR_STATUS": "I",
        "VENDOR_ID_OFFSET": "",  # empty → trailing comma
    }

    xml = client.execute_query(
        query_name="FM_VENDOR_MASTER",
        prompts=prompts,
        maxrows=10,
    )

    print("Raw XML preview:\n")
    print(xml[:1000], "\n...\n")

    rows = parse_executequery_xml(xml)
    print("First parsed row:\n")
    if rows:
        print(rows[0])
    else:
        print("[No rows returned]")
