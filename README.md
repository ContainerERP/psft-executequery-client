# psft-executequery-client

Small Python helper to call PeopleSoft **ExecuteQuery.v1** REST endpoints and parse XML results.

---

## Basic usage

```python
from psft_client import PeopleSoftClient, parse_executequery_xml

client = PeopleSoftClient(
    base_url="https://<host-or-ip>/PSIGW/RESTListeningConnector/PSFT_EP/ExecuteQuery.v1",
    auth=("PSREST", "your_password_here"),  # or ps_token="..."
    verify=False,  # dev only
)

xml = client.execute_query(
    query_name="FM_VENDOR_MASTER",
    prompts={"VENDOR_STATUS": "I", "VENDOR_ID_OFFSET": ""},
    maxrows=10,
)

rows = parse_executequery_xml(xml)
print(rows[0])


##  Notes

verify=False skips SSL certificate validation.
Use this only in DEV / test environments.
In PROD, point verify to a CA bundle or leave it as True.

The order of keys in prompts matters because PeopleSoft expects
names and values aligned:

prompt_uniquepromptname = A,B
prompt_fieldvalue       = 1,2
