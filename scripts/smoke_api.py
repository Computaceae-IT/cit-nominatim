#!/usr/bin/env python3
"""Read-only API contract smoke test, intended for an isolated staging URL."""
import argparse
import json
import urllib.parse
import urllib.request


def smoke(base_url, query="Geneve"):
    if urllib.parse.urlsplit(base_url).scheme not in ("http", "https"):
        raise ValueError("An http(s) staging URL is required")

    def get(path, params):
        url = base_url.rstrip("/") + path + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": "cit-nominatim-staging-smoke/1"})
        with urllib.request.urlopen(req, timeout=15) as response:
            result = json.load(response)
        if isinstance(result, dict) and "error" in result:
            raise ValueError(f"{path}: {result['error']}")
        return result

    status = get("/status.php", {"format": "json"})
    if not isinstance(status, dict) or status.get("status") != 0:
        raise ValueError("Database/API status is not healthy")
    places = get("/search.php", {"q": query, "format": "json", "limit": 1, "addressdetails": 1})
    if not isinstance(places, list) or not places:
        raise ValueError("Search must return a non-empty list for the agreed fixture")
    place = places[0]
    for key in ("lat", "lon", "osm_type", "osm_id", "display_name"):
        if key not in place:
            raise ValueError(f"Search is missing {key}")
    reverse = get("/reverse.php", {"lat": place["lat"], "lon": place["lon"], "format": "json", "addressdetails": 1})
    if not isinstance(reverse, dict) or not reverse.get("display_name"):
        raise ValueError("Reverse must return a named place")
    kind = {"node": "N", "way": "W", "relation": "R"}[place["osm_type"]]
    lookup = get("/lookup.php", {"osm_ids": kind + str(place["osm_id"]), "format": "json"})
    if not isinstance(lookup, list) or not lookup:
        raise ValueError("Lookup must return the searched OSM object")
    details = get("/details.php", {"osmtype": kind, "osmid": place["osm_id"], "format": "json"})
    if not isinstance(details, dict) or "place_id" not in details:
        raise ValueError("Details must identify a place")
    return {"status": "OK", "query": query, "osm_type": place["osm_type"], "osm_id": place["osm_id"]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base_url")
    parser.add_argument("--query", default="Geneve")
    args = parser.parse_args()
    print(json.dumps(smoke(args.base_url, args.query), ensure_ascii=False))
