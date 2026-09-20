"""Instagram par carousel post karta hai (Instagram API with Instagram Login)."""
import os
import time

import requests

API_BASE = os.environ.get("IG_API_BASE", "https://graph.instagram.com/v23.0")


def _check(resp: requests.Response) -> dict:
    try:
        data = resp.json()
    except ValueError:
        raise RuntimeError(f"Instagram API ne non-JSON diya: {resp.status_code} {resp.text[:200]}")
    if resp.status_code >= 400 or "error" in data:
        raise RuntimeError(f"Instagram API error: {data.get('error', data)}")
    return data


def _wait_until_ready(container_id: str, token: str, tries: int = 20, delay: int = 5) -> None:
    for _ in range(tries):
        r = requests.get(
            f"{API_BASE}/{container_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        status = _check(r).get("status_code")
        if status == "FINISHED":
            return
        if status in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Container {container_id} status: {status}")
        time.sleep(delay)
    raise RuntimeError(f"Container {container_id} time par ready nahi hua")


def post_carousel(image_urls: list[str], caption: str) -> str:
    ig_id = os.environ["IG_USER_ID"]
    token = os.environ["IG_ACCESS_TOKEN"]
    if not 2 <= len(image_urls) <= 10:
        raise ValueError("Carousel mein 2 se 10 images hoti hain")

    # 1) har slide ka child container
    children = []
    for url in image_urls:
        r = requests.post(
            f"{API_BASE}/{ig_id}/media",
            data={"image_url": url, "is_carousel_item": "true", "access_token": token},
            timeout=60,
        )
        child_id = _check(r)["id"]
        _wait_until_ready(child_id, token)
        children.append(child_id)
        print(f"[publish] child ready: {child_id}")

    # 2) carousel container
    r = requests.post(
        f"{API_BASE}/{ig_id}/media",
        data={
            "media_type": "CAROUSEL",
            "children": ",".join(children),
            "caption": caption,
            "access_token": token,
        },
        timeout=60,
    )
    container_id = _check(r)["id"]
    _wait_until_ready(container_id, token)

    # 3) publish
    r = requests.post(
        f"{API_BASE}/{ig_id}/media_publish",
        data={"creation_id": container_id, "access_token": token},
        timeout=60,
    )
    media_id = _check(r)["id"]
    print(f"[publish] posted! media id: {media_id}")
    return media_id
