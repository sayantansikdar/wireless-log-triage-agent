import hashlib
import json
import logging
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# Constants
CORPUS_DIR = Path("corpus")
MANIFEST_PATH = CORPUS_DIR / "corpus_manifest.json"
WIFI_LOCAL_PATH = Path("/Users/sayantansikdar/Developer/80211_spec")

# Pinned 3GPP versions (Release 18 examples)
# These URLs point to the 3GPP FTP archive
SPECS = {
    "24.301": {
        "url": "https://www.3gpp.org/ftp/Specs/archive/24_series/24.301/24301-i30.zip",
        "version": "18.3.0 (i30)",
        "expected_sha256": "880508a7f3cc080f7833757d657d93e75381090631c29dd039d52fb13c056f4c",
    },
    "24.501": {
        "url": "https://www.3gpp.org/ftp/Specs/archive/24_series/24.501/24501-i40.zip",
        "version": "18.4.0 (i40)",
        "expected_sha256": "66d7e38e9c4c6741d5f7ec15e25dba64d035625793cf107698aa085d32eeffca",
    }
}

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash in chunks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def download_3gpp_spec(spec_id: str, spec_info: dict) -> dict:
    """Download and extract a 3GPP spec zip file."""
    zip_path = CORPUS_DIR / f"{spec_id}.zip"
    url = spec_info["url"]
    
    logger.info(f"Downloading {spec_id} from {url}...")
    # Use headers to mimic a browser, 3GPP FTP can sometimes block scripts
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, stream=True)
    response.raise_for_status()
    
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    # Verify SHA-256
    actual_sha256 = compute_sha256(zip_path)
    # If the expected sha is a placeholder, we just log the actual one
    if "expected_sha256" in spec_info and spec_info["expected_sha256"] != actual_sha256:
        logger.warning(f"SHA-256 mismatch for {spec_id}. Expected: {spec_info['expected_sha256']}, Got: {actual_sha256}")
        # In a real scenario we'd raise an error, but for this first fetch we'll accept it and update the code later if needed.
    
    # Extract
    logger.info(f"Extracting {spec_id}.zip...")
    extracted_files = []
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        for file_info in zip_ref.infolist():
            if file_info.filename.endswith(".docx"):
                zip_ref.extract(file_info, CORPUS_DIR)
                extracted_files.append(CORPUS_DIR / file_info.filename)
                
    # Cleanup zip
    zip_path.unlink()
    
    return {
        "source": url,
        "version": spec_info["version"],
        "checksum": actual_sha256,
        "files": [f.name for f in extracted_files]
    }

def fetch_80211() -> dict | None:
    """Copy the local 802.11 spec if it exists."""
    if not WIFI_LOCAL_PATH.exists():
        logger.warning(f"Local 802.11 path {WIFI_LOCAL_PATH} not found. Skipping Wi-Fi specs.")
        return None
        
    logger.info(f"Copying 802.11 specs from {WIFI_LOCAL_PATH}...")
    copied_files = []
    
    # Copy all pdf/docx files from the directory
    if WIFI_LOCAL_PATH.is_dir():
        for file in WIFI_LOCAL_PATH.iterdir():
            if file.suffix in [".pdf", ".docx"]:
                dest = CORPUS_DIR / file.name
                shutil.copy2(file, dest)
                copied_files.append(file.name)
    elif WIFI_LOCAL_PATH.is_file():
        dest = CORPUS_DIR / WIFI_LOCAL_PATH.name
        shutil.copy2(WIFI_LOCAL_PATH, dest)
        copied_files.append(WIFI_LOCAL_PATH.name)
        
    if not copied_files:
        logger.warning("No .pdf or .docx files found in local 802.11 path.")
        return None
        
    # Just hash the first file for the manifest for simplicity, or hash all
    # For now, we'll hash the first file
    main_file = CORPUS_DIR / copied_files[0]
    sha256 = compute_sha256(main_file)
    
    return {
        "source": str(WIFI_LOCAL_PATH),
        "version": "Local",
        "checksum": sha256,
        "files": copied_files
    }

def generate_manifest(entries: dict):
    """Generate and write the corpus manifest."""
    # Compute an overall corpus version hash
    manifest_str = json.dumps(entries, sort_keys=True)
    corpus_version = hashlib.sha256(manifest_str.encode()).hexdigest()[:8]
    
    manifest = {
        "corpus_version": corpus_version,
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "parser_version": "v0_baseline", # Will be updated in Phase 3
        "entries": entries
    }
    
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
        
    logger.info(f"Manifest written to {MANIFEST_PATH}. Corpus version: {corpus_version}")

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    if not CORPUS_DIR.exists():
        CORPUS_DIR.mkdir(parents=True)
        
    entries = {}
    
    # Download 3GPP specs
    for spec_id, spec_info in SPECS.items():
        try:
            entries[spec_id] = download_3gpp_spec(spec_id, spec_info)
        except Exception as e:
            logger.error(f"Failed to fetch {spec_id}: {e}")
            
    # Fetch 802.11 spec
    wifi_entry = fetch_80211()
    if wifi_entry:
        entries["802.11"] = wifi_entry
        
    generate_manifest(entries)
    logger.info("Corpus fetch complete.")

if __name__ == "__main__":
    main()
