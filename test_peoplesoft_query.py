from psft_client import PeopleSoftClient, parse_executequery_xml

client = PeopleSoftClient(
    base_url="https://192.168.232.228/PSIGW/RESTListeningConnector/PSFT_EP/ExecuteQuery.v1",
    auth=("your userid", "yourpassword"),   # or ps_token="..."
    verify=False,                            # dev only
)

prompts = {
    "VENDOR_STATUS": "I",
    "VENDOR_ID_OFFSET": "",
}

xml = client.execute_query("FM_VENDOR_MASTER", prompts, maxrows=50)

rows = parse_executequery_xml(xml)
for r in rows[:5]:
    print(r["VENDOR_ID"], r["VENDOR_NAME_SHORT"])
