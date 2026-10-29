#!/usr/bin/env python3
"""Collect attributed news headlines and optional football fixtures into data/news.json."""
import json, os, re, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "news.json"
UA = "CurrentBenchNewsCollector/1.0 (+https://github.com/Adura2410/Current-bench-)"
FEEDS = [
    ("Nigeria", "Google News Nigeria", "https://news.google.com/rss/search?q=Nigeria+news&hl=en-NG&gl=NG&ceid=NG:en"),
    ("Politics", "Google News Nigeria Politics", "https://news.google.com/rss/search?q=Nigeria+politics&hl=en-NG&gl=NG&ceid=NG:en"),
    ("Business", "Google News Nigeria Business", "https://news.google.com/rss/search?q=Nigeria+business+economy&hl=en-NG&gl=NG&ceid=NG:en"),
    ("Entertainment", "Google News Nigeria Entertainment", "https://news.google.com/rss/search?q=Nigeria+entertainment&hl=en-NG&gl=NG&ceid=NG:en"),
    ("Entertainment", "Google News Nigerian Nollywood", "https://news.google.com/rss/search?q=Nollywood+OR+%22Nigerian+film%22+OR+%22Nigerian+actor%22&hl=en-NG&gl=NG&ceid=NG:en"),
    ("Entertainment", "Google News Nigerian music and Afrobeats", "https://news.google.com/rss/search?q=Afrobeats+OR+%22Nigerian+music%22+OR+%22Nigerian+singer%22&hl=en-NG&gl=NG&ceid=NG:en"),
    ("Entertainment", "Google News Nigerian celebrities", "https://news.google.com/rss/search?q=%22Nigerian+celebrity%22+OR+%22Nigerian+entertainment%22+OR+Nollywood+celebrity&hl=en-NG&gl=NG&ceid=NG:en"),
    ("Football", "Google News Football", "https://news.google.com/rss/search?q=world+football+soccer&hl=en&gl=US&ceid=US:en"),
    ("World", "Google News World", "https://news.google.com/rss/search?q=world+news&hl=en&gl=US&ceid=US:en"),
    ("Technology", "Google News Technology", "https://news.google.com/rss/search?q=technology+news&hl=en&gl=US&ceid=US:en"),
    ("Africa", "Google News Africa", "https://news.google.com/rss/search?q=Africa+news&hl=en&gl=NG&ceid=NG:en"),
    ("World", "BBC World", "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("World", "BBC Africa", "https://feeds.bbci.co.uk/news/world/africa/rss.xml"),
    ("Business", "BBC Business", "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("Technology", "BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml"),
    ("World", "Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml"),
    ("Nigeria", "Premium Times Nigeria", "https://www.premiumtimesng.com/feed"),
    ("Nigeria", "The Guardian Nigeria", "https://guardian.ng/feed/"),
    ("Nigeria", "Punch Nigeria", "https://punchng.com/feed/"),
    ("World", "DW Top Stories", "https://rss.dw.com/rdf/rss-en-all"),
]
def request(url, headers=None, timeout=18):
    h={"User-Agent":UA,"Accept":"application/rss+xml, application/xml, application/json, text/xml, */*"}
    if headers: h.update(headers)
    req=urllib.request.Request(url,headers=h)
    with urllib.request.urlopen(req,timeout=timeout) as res:
        return res.read()
def clean_html(value):
    value=re.sub(r"<(script|style)[^>]*>.*?</\1>"," ",value or "",flags=re.I|re.S)
    value=re.sub(r"<[^>]+>"," ",value)
    return re.sub(r"\s+"," ",unescape(value)).strip()
def parse_date(value):
    if not value:return None
    try:
        d=parsedate_to_datetime(value)
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc).isoformat()
    except Exception:
        try:return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc).isoformat()
        except Exception:return None
def tag_text(node, names):
    for el in node.iter():
        if el.tag.split("}")[-1].lower() in names and el.text and el.text.strip():
            return el.text.strip()
    return ""
def read_feed(category, source, url):
    try:
        root=ET.fromstring(request(url))
        items=[]
        for item in root.iter():
            if item.tag.split("}")[-1].lower() not in ("item","entry"):continue
            title=clean_html(tag_text(item,{"title"}))
            link=""
            for el in item.iter():
                if el.tag.split("}")[-1].lower()=="link":
                    link=el.attrib.get("href","") or (el.text or "").strip()
                    if link:break
            summary=clean_html(tag_text(item,{"description","summary","encoded","content"}))
            published=parse_date(tag_text(item,{"pubdate","published","updated","date"}))
            if title and link.startswith(("https://","http://")):
                items.append({"title":title,"summary":summary[:420],"url":link,"published":published,"source":source,"category":category,"categories":[category]})
        print(f"{source}: {len(items)} headlines")
        return items
    except Exception as exc:
        print(f"Feed skipped: {source}: {exc}")
        return []
def newscentral_articles():
    # News Central Site states its written stories are CC BY 4.0 and may be
    # republished in full with credit and a link to the original story.
    # Its terms exclude photographs, so this collector stores text only.
    url="https://newscentral.site/feed/en.json"
    try:
        data=json.loads(request(url,timeout=20))
        out=[]
        for item in data.get("items",[]):
            title=clean_html(item.get("title",""))
            link=item.get("url") or item.get("external_url") or ""
            if not title or not link.startswith(("https://","http://")):
                continue
            tags=item.get("tags") or []
            tag_text_value=" ".join(str(t.get("name","") if isinstance(t,dict) else t) for t in tags)
            searchable=(title+" "+clean_html(item.get("summary",""))+" "+tag_text_value).lower()
            if any(w in searchable for w in ("nollywood","afrobeats","celebrity","entertainment","film","music")):
                category="Entertainment"
            elif any(w in searchable for w in ("football","soccer","premier league","champions league","matchday")):
                category="Football"
            elif any(w in searchable for w in ("business","market","economy","finance","company","trade")):
                category="Business"
            elif any(w in searchable for w in ("politic","election","president","parliament","government","minister")):
                category="Politics"
            elif any(w in searchable for w in ("technology","tech","artificial intelligence","software","cyber")):
                category="Technology"
            elif any(w in searchable for w in ("nigeria","nigerian","lagos","abuja","west africa")):
                category="Nigeria"
            else:
                category="World"
            raw=item.get("content_text") or item.get("content_html") or item.get("summary") or ""
            body=clean_html(raw)[:20000]
            article={
                "title":title,
                "summary":clean_html(item.get("summary",""))[:700],
                "url":link,
                "published":parse_date(item.get("date_published") or item.get("date_modified")),
                "source":"News Central Site (CC BY 4.0)",
                "category":category,
                "categories":[category],
            }
            if body:
                article["content"]=body
                article["content_type"]="cc_by_4.0"
            out.append(article)
        print(f"News Central Site CC BY 4.0: {len(out)} stories; {sum(1 for x in out if x.get('content'))} with text")
        return out
    except Exception as exc:
        print(f"News Central Site feed skipped: {exc}")
        return []
def gdelt_articles():
    # GDELT DOC API is a supplemental open global-news search endpoint; no API key is required.
    q='(Nigeria OR Nigerian) (politics OR economy OR business OR government OR election)'
    url="https://api.gdeltproject.org/api/v2/doc/doc?"+urllib.parse.urlencode({"query":q,"mode":"ArtList","format":"json","sort":"DateDesc","maxrecords":50})
    try:
        data=json.loads(request(url,timeout=25))
        out=[]
        for a in data.get("articles",[]):
            title=clean_html(a.get("title","")); link=a.get("url","")
            if title and link.startswith("http"):
                out.append({"title":title,"summary":"","url":link,"published":parse_date(a.get("seendate","")),"source":a.get("domain","GDELT indexed publisher"),"category":"Nigeria","categories":["Nigeria","Politics"]})
        print(f"GDELT: {len(out)} headlines")
        return out
    except Exception as exc:
        print(f"GDELT skipped: {exc}");return []
def newsdata_articles():
    # Fetch ordinary Nigerian headlines and, separately, articles for which NewsData.io
    # reports a full-content field. Availability depends on the API plan and publisher.
    key=os.getenv("NEWSDATA_API_KEY","").strip()
    if not key:
        return []
    out=[]
    requests_to_make=[("headlines", {"country":"ng","language":"en","size":10})]
    # Enable only if the account plan permits the full-content filter (some keys return HTTP 403).
    if os.getenv("NEWSDATA_FULL_CONTENT","").strip()=="1":
        requests_to_make.append(("full-content", {"country":"ng","language":"en","full_content":1,"size":10}))
    for label, params in requests_to_make:
        query={"apikey":key, **params}
        url="https://newsdata.io/api/1/latest?"+urllib.parse.urlencode(query)
        try:
            data=json.loads(request(url,timeout=20))
            results=data.get("results") or []
            print(f"NewsData.io {label}: {len(results)} results")
            for a in results:
                title=clean_html(a.get("title","")); link=a.get("link","")
                if not title or not link.startswith(("https://","http://")):
                    continue
                cats=a.get("category") or []
                category="Nigeria"
                if any("business" in str(x).lower() for x in cats): category="Business"
                elif any("entertainment" in str(x).lower() for x in cats): category="Entertainment"
                elif any("politic" in str(x).lower() for x in cats): category="Politics"
                elif any(term in (title+" "+clean_html(a.get("description",""))).lower() for term in ("football","soccer","premier league")): category="Football"
                raw_content=a.get("content") or a.get("full_content") or ""
                if isinstance(raw_content, dict):
                    raw_content=raw_content.get("content") or raw_content.get("text") or raw_content.get("full_text") or ""
                content=clean_html(raw_content)[:20000] if isinstance(raw_content,str) else ""
                article={
                    "title":title,
                    "summary":clean_html(a.get("description",""))[:700],
                    "url":link,
                    "published":parse_date(a.get("pubDate")),
                    "source":(a.get("source_name") or "NewsData.io"),
                    "category":category,
                    "categories":[category],
                }
                if content:
                    article["content"]=content
                    article["content_type"]="provider_full_content"
                # Prefer the version with content if the same URL was returned twice.
                existing=next((i for i,x in enumerate(out) if x.get("url")==link),None)
                if existing is None:
                    out.append(article)
                elif content and not out[existing].get("content"):
                    out[existing]=article
        except Exception as exc:
            print(f"NewsData.io {label} request skipped: {exc}")
    print(f"NewsData.io: {len(out)} unique headlines; {sum(1 for item in out if item.get('content'))} with content text")
    return out
def guardian_articles():
    # Optional official publisher API; obey the Guardian Open Platform terms and attribution rules.
    key=os.getenv("GUARDIAN_API_KEY","").strip()
    if not key:
        return []
    url="https://content.guardianapis.com/search?"+urllib.parse.urlencode({"api-key":key,"order-by":"newest","page-size":50,"show-fields":"trailText"})
    try:
        data=json.loads(request(url,timeout=20)); out=[]
        for a in (data.get("response") or {}).get("results",[]):
            title=clean_html(a.get("webTitle","")); link=a.get("webUrl","")
            if title and link.startswith("http"):
                section=(a.get("sectionName") or "World")
                low=section.lower()
                category="Business" if "business" in low else ("Politics" if "politic" in low else ("Technology" if "technology" in low else "World"))
                out.append({"title":title,"summary":clean_html((a.get("fields") or {}).get("trailText",""))[:420],"url":link,"published":parse_date(a.get("webPublicationDate")),"source":"The Guardian","category":category,"categories":[category]})
        print(f"The Guardian API: {len(out)} headlines")
        return out
    except Exception as exc:
        print(f"The Guardian API skipped: {exc}");return []
def football_matches():
    token=os.getenv("FOOTBALL_DATA_TOKEN","").strip()
    if not token:
        print("Football API not configured: set GitHub secret FOOTBALL_DATA_TOKEN to enable fixtures.")
        return []
    competitions=(os.getenv("FOOTBALL_COMPETITIONS") or "PL,PD,BL1,SA,FL1,CL,EL,DED,PPL,CLI").split(",")
    matches=[]
    # football-data.org competition codes: free-tier availability depends on the account's current plan.
    for code in [c.strip() for c in competitions if c.strip()][:12]:
        try:
            raw=json.loads(request("https://api.football-data.org/v4/competitions/"+urllib.parse.quote(code)+"/matches?status=SCHEDULED,LIVE,IN_PLAY,PAUSED,FINISHED",headers={"X-Auth-Token":token},timeout=20))
            for m in raw.get("matches",[]):
                home=(m.get("homeTeam") or {}).get("name","Home")
                away=(m.get("awayTeam") or {}).get("name","Away")
                score=m.get("score") or {}
                ft=score.get("fullTime") or {}
                scoretext=(str(ft.get("home"))+" - "+str(ft.get("away"))) if ft.get("home") is not None and ft.get("away") is not None else "—"
                matches.append({"competition":(m.get("competition") or {}).get("name",code),"date":m.get("utcDate"),"home":home,"away":away,"score":scoretext,"status":m.get("status","")})
            time.sleep(.15)
        except Exception as exc:print(f"Football competition {code} skipped: {exc}")
    return matches
def main():
    articles=[]
    for category,source,url in FEEDS:articles.extend(read_feed(category,source,url))
    articles.extend(newscentral_articles())
    articles.extend(gdelt_articles())
    articles.extend(newsdata_articles())
    articles.extend(guardian_articles())
    unique={}
    for a in articles:
        key=re.sub(r"\W+"," ",a["title"].lower()).strip()
        if not key: continue
        incoming=list(dict.fromkeys([str(c) for c in (a.get("categories") or []) if c]))
        if a.get("category") and a["category"] not in incoming:
            incoming.append(a["category"])
        if key not in unique:
            a["categories"]=incoming
            unique[key]=a
            continue
        # A headline may arrive from multiple topic feeds. Keep every supported
        # category instead of letting whichever feed runs first decide its section.
        current=unique[key]
        merged=list(dict.fromkeys((current.get("categories") or [])+incoming))
        if current.get("category") and current["category"] not in merged:
            merged.append(current["category"])
        if a.get("category") and a["category"] not in merged:
            merged.append(a["category"])
        current["categories"]=merged
        if a.get("content") and not current.get("content"):
            a["categories"]=merged
            unique[key]=a
    articles=list(unique.values())
    articles.sort(key=lambda x:x.get("published") or "",reverse=True)
    # Keep a broad rotating window, but do not scrape full article bodies or publisher images.
    payload={"generated_at":datetime.now(timezone.utc).isoformat(),"articles":articles[:300],"matches":football_matches(),"providers":{"rss":"partial; some feeds may be unavailable","gdelt":"attempted","football_data_org":"enabled" if os.getenv("FOOTBALL_DATA_TOKEN") else "awaiting optional secret"}}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Wrote {min(len(articles),300)} unique headlines to {OUT}")
if __name__=="__main__":main()
