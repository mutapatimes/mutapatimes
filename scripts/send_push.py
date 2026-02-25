#!/usr/bin/env python3
"""Send FCM push notification for breaking/spotlight news.

Called by the fetch-news GitHub Action after updating spotlight.json.
Uses the FCM v1 API with service account authentication.
Requires FIREBASE_SERVICE_ACCOUNT secret (JSON).
"""
import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

FIREBASE_SA_JSON = os.environ.get("FIREBASE_SERVICE_ACCOUNT", "")
SPOTLIGHT_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "spotlight.json")
MAX_AGE_HOURS = 3  # Match the cron interval
FORCE_PUSH = os.environ.get("FORCE_PUSH", "") == "1"


def _b64url(data):
    """Base64url encode without padding."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.urlsafe_b64encode(data).rstrip(b"=")


def _int_to_bytes(n, length):
    """Convert integer to big-endian bytes."""
    return n.to_bytes(length, byteorder="big")


def _rsa_sign_pkcs1_sha256(private_key_pem, message):
    """Sign a message with RSA PKCS#1 v1.5 SHA-256 using pure Python.

    Parses a PKCS#8 PEM private key and performs RSA signing.
    """
    # Decode PEM
    lines = private_key_pem.strip().split("\n")
    b64 = "".join(l for l in lines if not l.startswith("-----"))
    der = base64.b64decode(b64)

    # Parse PKCS#8 wrapper to get RSA private key
    # PKCS#8 structure: SEQUENCE { version, algorithmIdentifier, privateKey }
    def parse_asn1(data, offset=0):
        tag = data[offset]
        offset += 1
        length = data[offset]
        offset += 1
        if length & 0x80:
            num_bytes = length & 0x7F
            length = int.from_bytes(data[offset:offset + num_bytes], "big")
            offset += num_bytes
        return tag, length, offset

    # Skip outer SEQUENCE
    _, _, pos = parse_asn1(der, 0)
    # Skip version INTEGER
    tag, vlen, pos = parse_asn1(der, pos)
    pos += vlen
    # Skip algorithmIdentifier SEQUENCE
    tag, alen, pos = parse_asn1(der, pos)
    pos += alen
    # Get privateKey OCTET STRING
    tag, pklen, pos = parse_asn1(der, pos)
    rsa_der = der[pos:pos + pklen]

    # Parse RSA private key (PKCS#1)
    def parse_integer(data, offset):
        tag, length, offset = parse_asn1(data, offset)
        value = int.from_bytes(data[offset:offset + length], "big")
        return value, offset + length

    # Skip outer SEQUENCE
    _, _, pos = parse_asn1(rsa_der, 0)
    # Parse: version, n, e, d, p, q, dp, dq, qinv
    version, pos = parse_integer(rsa_der, pos)
    n, pos = parse_integer(rsa_der, pos)
    e, pos = parse_integer(rsa_der, pos)
    d, pos = parse_integer(rsa_der, pos)

    # RSA signature: PKCS#1 v1.5
    digest = hashlib.sha256(message if isinstance(message, bytes) else message.encode()).digest()

    # DigestInfo for SHA-256
    digest_info = (
        b"\x30\x31\x30\x0d\x06\x09\x60\x86\x48\x01\x65\x03\x04\x02\x01\x05\x00\x04\x20"
        + digest
    )

    k = (n.bit_length() + 7) // 8
    ps_len = k - len(digest_info) - 3
    em = b"\x00\x01" + (b"\xff" * ps_len) + b"\x00" + digest_info

    m_int = int.from_bytes(em, "big")
    s_int = pow(m_int, d, n)
    return _int_to_bytes(s_int, k)


def get_access_token(sa_info):
    """Get OAuth2 access token from service account credentials."""
    now = int(time.time())
    header = json.dumps({"alg": "RS256", "typ": "JWT"})
    payload = json.dumps({
        "iss": sa_info["client_email"],
        "scope": "https://www.googleapis.com/auth/firebase.messaging "
                 "https://www.googleapis.com/auth/datastore",
        "aud": "https://oauth2.googleapis.com/token",
        "iat": now,
        "exp": now + 3600,
    })

    signing_input = _b64url(header) + b"." + _b64url(payload)
    signature = _rsa_sign_pkcs1_sha256(sa_info["private_key"], signing_input)
    jwt_token = (signing_input + b"." + _b64url(signature)).decode("utf-8")

    data = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant_type:jwt-bearer",
        "assertion": jwt_token,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    resp = urllib.request.urlopen(req, timeout=15)
    return json.loads(resp.read().decode("utf-8"))["access_token"]


def _parse_date(s):
    """Try to parse an ISO-ish date string."""
    if not s:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(s.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def get_tokens_from_firestore(project_id, access_token):
    """Read push tokens from Firestore REST API."""
    url = (
        f"https://firestore.googleapis.com/v1/projects/{project_id}"
        f"/databases/(default)/documents/push_tokens?pageSize=500"
    )
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"Failed to read Firestore: {e}")
        return []
    tokens = []
    for doc in data.get("documents", []):
        fields = doc.get("fields", {})
        token = fields.get("token", {}).get("stringValue", "")
        if token:
            tokens.append(token)
    return tokens


def send_push(project_id, access_token, title, body, url, tokens):
    """Send push notifications via FCM v1 API."""
    endpoint = (
        f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    )
    sent = 0
    for token in tokens:
        payload = json.dumps({
            "message": {
                "token": token,
                "notification": {
                    "title": title,
                    "body": body,
                    "image": "https://www.mutapatimes.com/img/android-icon-192x192.png",
                },
                "webpush": {
                    "fcm_options": {
                        "link": url,
                    }
                },
            }
        }).encode("utf-8")
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            },
        )
        try:
            resp = urllib.request.urlopen(req, timeout=10)
            json.loads(resp.read().decode("utf-8"))
            sent += 1
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="replace")
            print(f"FCM error ({e.code}): {err_body}")
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            print(f"Failed to send to token: {e}")
    print(f"Push sent to {sent}/{len(tokens)} devices")


def main():
    if not FIREBASE_SA_JSON:
        print("No FIREBASE_SERVICE_ACCOUNT set, skipping push.")
        return

    sa_info = json.loads(FIREBASE_SA_JSON)
    project_id = sa_info["project_id"]

    if not os.path.exists(SPOTLIGHT_PATH):
        print("No spotlight.json found, skipping push.")
        return

    with open(SPOTLIGHT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    articles = data.get("articles", [])
    if not articles:
        print("No spotlight articles, skipping push.")
        return

    top = articles[0]
    pub_date = _parse_date(
        top.get("publishedAt") or top.get("published_at") or top.get("date", "")
    )
    now = datetime.now(timezone.utc)

    if not FORCE_PUSH and pub_date and (now - pub_date).total_seconds() > MAX_AGE_HOURS * 3600:
        print(f"Top article too old ({pub_date}), skipping push.")
        return
    if FORCE_PUSH:
        print("FORCE_PUSH enabled, bypassing age check.")

    print("Authenticating with Firebase service account...")
    access_token = get_access_token(sa_info)

    tokens = get_tokens_from_firestore(project_id, access_token)
    if not tokens:
        print("No push tokens found, skipping.")
        return

    title_text = top.get("title", "Breaking News")[:80]
    body_text = top.get("description", "")[:150]
    article_url = top.get("url", "https://www.mutapatimes.com/")

    send_push(
        project_id=project_id,
        access_token=access_token,
        title=f"Breaking: {title_text}",
        body=body_text,
        url=article_url,
        tokens=tokens,
    )


if __name__ == "__main__":
    main()
