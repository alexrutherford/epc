import os
import base64
import requests
from tqdm import tqdm
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional

load_dotenv(override=True)

API_DOMESTIC = "https://epc.opendatacommunities.org/api/v1/domestic/search"
API_DISPLAY = "https://epc.opendatacommunities.org/api/v1/display/search"

CertRow = Dict[str, Any]

def get_auth_header() -> Dict[str, str]:
    """
    Build the Basic Auth header from environment variables.
    Requires EPC_EMAIL and EPC_API_KEY in the environment.
    """
    email = os.getenv("EPC_EMAIL")
    api_key = os.getenv("EPC_API_KEY")
    if not email or not api_key:
        raise ValueError("Missing EPC_EMAIL or EPC_API_KEY environment variables")
    token = base64.b64encode(f"{email}:{api_key}".encode()).decode()
    return {"Authorization": f"Basic {token}"}

def fetch_certificates(
    api_url: str, 
    postcode: str, 
    auth_header: Dict[str, str]
) -> List[CertRow]:
    all_rows = []
    page = 0
    page_size = 100  # Adjust as needed, API default is often 100

    while True:
        resp = requests.get(
            api_url,
            params={
                "postcode": postcode,
                "page": page,
                "size": page_size
            },
            headers={**auth_header, "Accept": "application/json"}
        )
        resp.raise_for_status()
        data = resp.json()
        rows = data.get("rows", []) if isinstance(data.get("rows"), list) else []
        if not rows:
            break
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        page += 1

    return all_rows
 
    resp.raise_for_status()

    #print(resp.status_code)
    #print(resp.text)

    data = resp.json()
    return data.get("rows", []) if isinstance(data.get("rows"), list) else []

def download_html(
    url: str, 
    target_folder: str, 
    auth_header: Dict[str, str]
) -> str:
    resp = requests.get(url, headers=auth_header)
    resp.raise_for_status()
    filename = url.rstrip("/").split("/")[-1] + ".html"
    path = os.path.join(target_folder, filename)
    print('PATH:',path)
    with open(path, "wb") as f:
        f.write(resp.content)
    return path

def write_json(blob: Dict,uprn: str,postcode:str) -> None:

    """
    Write a JSON blob to a file named after the UPRN.
    """
    filename = f"{uprn}.json"
    path = os.path.join('data',postcode, filename)
    with open(path, "w") as f:
        import json
        json.dump(blob, f, indent=2)
    print(f"JSON data written to {filename}")

def main() -> None:
    auth_header = get_auth_header()

    postcode: str = input("Enter UK postcode (e.g. SW1A 1AA): ").strip()
    os.makedirs(os.path.join('data', postcode), exist_ok=True)

    all_certs: List[CertRow] = []
    for api in [API_DOMESTIC]:
        all_certs.extend(fetch_certificates(api, postcode, auth_header))

    if not all_certs:
        print(f"No EPC certificates found for postcode {postcode}")
        return

    print(f"Found {len(all_certs)} certificates. Downloading...")
    for cert in tqdm(all_certs):
        try:
            write_json(cert, cert.get("uprn", "unknown"), postcode)
        except Exception as e:
                tqdm.write(f"❌ Failed to write : {str(e)}")
        """url: Optional[str] = cert.get("url")
        if url:
            try:
                path = download_html(url, postcode, auth_header)
                tqdm.write(f"✅ Saved: {path}")
            except Exception as e:
                tqdm.write(f"❌ Failed to download {url}: {e}")
        else:
            sorted_keys = ", ".join(sorted(cert.keys()))
            tqdm.write(f"❌ No URL found for certificate: {sorted_keys}")"""
if __name__ == "__main__":
    main()
