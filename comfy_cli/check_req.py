import json
import traceback
from urllib import request
import urllib.error
import urllib.parse
import uuid
import joblib
import os

from rich import print as pprint


def queue(host, port, workflow, client_id, req=None):
    data = {"prompt": workflow, "client_id": client_id}
    if req is None:
        req = request.Request(f"http://{host}:{port}/prompt", json.dumps(data).encode("utf-8"))
    
    try:
        print(f"Request: {req}")
        print("URL:", req.full_url)
        print("Method:", req.get_method())
        print("Headers:", dict(req.header_items()))
        print("Data (body):", req.data)
        print("Host:", req.host)
        print("Origin req host:", req.origin_req_host)
        print("Unredirected headers:", req.unredirected_hdrs)
        resp = request.urlopen(req)
        body = json.loads(resp.read())

        prompt_id = body["prompt_id"]
        print(f"Prompt ID: {prompt_id}")
    except urllib.error.HTTPError as e:
        traceback.print_exc()
        message = "An unknown error occurred"
        if e.status == 500:
            # This is normally just the generic internal server error
            message = e.read().decode()
        elif e.status == 400:
            # Bad Request - workflow failed validation on the server
            body = json.loads(e.read())
            if body["node_errors"].keys():
                message = json.dumps(body["node_errors"], indent=2)

        pprint(f"[bold red]Error running workflow\n{message}[/bold red]")
        raise Exception(message)
    
if __name__ == "__main__":
    # with open("/home/kpavel/Downloads/check_wf.json", "r") as f:
    #     json_data = json.loads(f.read())
    req = joblib.load("/home/kpavel/Downloads/media_req.joblib")
    
    queue("127.0.0.1", "8188", None, "test_111", req=req)
    