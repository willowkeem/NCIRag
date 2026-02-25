import time, json, os, re, hashlib
from urllib.parse import urljoin, urlparse, urldefrag
import requests
from bs4 import BeautifulSoup
import urllib.robotparser as robotparser

# -----------------------------
# Crawl scope + filtering rules 
# -----------------------------

# Restrict to NCI course information related paths
ALLOWED_PREFIXES = [
    "https://www.ncirl.ie/Study/",          # Course listings, tuition fees, entry requirements, etc.
    "https://www.ncirl.ie/Students/"
    "https://www.ncirl.ie/Courses/"
    "https://www.ncirl.ie/Careers/",        # Detailed course pages
    "https://www.ncirl.ie/International/", # Additional info for international students
]

SEED = "https://www.ncirl.ie/"

# Key keywords to be included in the URL
URL_KEYWORDS_ALLOW = [
    "courses",
    "course-details",
    "undergraduate",
    "postgraduate",
    "fees",
    "entry-requirements",
]

# Unnecesary pages to exclude (Noise filtering)
URL_KEYWORDS_BLOCK = [
    "news", "events", "privacy", "cookies", "search", "login", "sitemap",
    "people", "library", "whatson", "connected", "alumni", "chaplaincy",
    "healthy", "dts", "president", "governance", "loop", "vacancies", "blog",
]

# File extensions to exclude from download
SKIP_EXTS = (
    ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp",
    ".zip", ".rar", ".7z",
    ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
)

# Seed URL and domain configuration
SEED = "https://www.ncirl.ie/Study/All-Courses"
DOMAIN = "ncirl.ie"

# Output locations
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTDIR = os.path.join(BASE_DIR, "data", "raw")
HTMLDIR = os.path.join(OUTDIR, "html")
MANIFEST = os.path.join(OUTDIR, "manifest.jsonl")

# Crawl controls
DELAY = 0.5  # Set a delay to reduce server load
MAX_PAGES = 500
MAX_DEPTH = 3  
TIMEOUT = 15

# User Agent 
USER_AGENT = "NCI-RAG-Bot/0.1 (x23413701@student.ncirl.ie)"

os.makedirs(OUTDIR, exist_ok=True)
os.makedirs(HTMLDIR, exist_ok=True)


# robots.txt 
rp = robotparser.RobotFileParser()
rp.set_url("https://www.ncirl.ie/robots.txt")
try:
    rp.read()
except Exception:
    rp = None

def allowed_by_robots(url: str) -> bool:
    return rp.can_fetch(USER_AGENT, url) if rp else True

def normalize_url(url: str) -> str:
    url, _ = urldefrag(url)
    url = (url or "").strip()
    p = urlparse(url)
    if p.path != "/" and url.endswith("/"):
        url = url[:-1]
    return url

def same_domain(url: str) -> bool:
    netloc = (urlparse(url).netloc or "").lower()
    return netloc == DOMAIN or netloc.endswith("." + DOMAIN)

def contains_any(text: str, words) -> bool:
    t = (text or "").lower()
    return any(w and (w.lower() in t) for w in words)

def starts_with_any(url: str, prefixes) -> bool:
    u = normalize_url(url).rstrip("/")
    for p in prefixes:
        p2 = normalize_url(p).rstrip("/")
        if u == p2 or u.startswith(p2 + "/"):
            return True
    return False

def should_follow(next_url: str) -> bool:
    if not next_url: return False
    if not same_domain(next_url): return False

    u = next_url.lower()
    if urlparse(next_url).path.lower().endswith(SKIP_EXTS):
        return False

    if contains_any(u, URL_KEYWORDS_BLOCK):
        return False

    # Collect only if it starts with ALLOWED_PREFIXES or contains key keywords
    if starts_with_any(next_url, ALLOWED_PREFIXES):
        return True
    
    if contains_any(u, URL_KEYWORDS_ALLOW):
        return True

    return False

def url_to_filename(url: str, ext: str = ".html") -> str:
    u = normalize_url(url)
    name = u.replace("://", "___").replace("/", "_")
    name = re.sub(r"[^A-Za-z0-9_\-\.]", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")
    h = hashlib.sha1(u.encode("utf-8")).hexdigest()[:10]
    max_base = 180
    if len(name) > max_base: name = name[:max_base].rstrip("_")
    return f"{name}__{h}{ext}"

def guess_ext_from_url_or_mime(url: str, mime: str) -> str:
    path = urlparse(url).path
    if "." in path:
        ext = "." + path.split(".")[-1].lower()
        if 1 <= len(ext) <= 6: return ext
    if mime:
        m = mime.lower()
        if "pdf" in m: return ".pdf"
        if "text/plain" in m: return ".txt"
    return ".bin"

def save_bytes_as_urlname(url: str, content: bytes, mime: str):
    is_html = mime and "html" in mime.lower()
    ext = ".html" if is_html else guess_ext_from_url_or_mime(url, mime)
    fn = url_to_filename(url, ext=ext)
    path = os.path.join(HTMLDIR if is_html else OUTDIR, fn)
    with open(path, "wb") as f:
        f.write(content)
    return fn, path

def extract_clean_text(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for noise in soup(['nav', 'footer', 'header', 'script', 'style', 'aside']):
        noise.decompose()
    main_content = soup.find('main') or soup.find('article') or soup.find(id='content')
    if main_content:
        text = main_content.get_text(separator='\n', strip=True)
    else:
        text = soup.get_text(separator='\n', strip=True)
    return text

# Crawl loop
seen = set()
to_visit = [(normalize_url(SEED), 0)]
pages_saved = 0

print(f"Starting crawl at {SEED}...")

with open(MANIFEST, "a", encoding="utf8") as mf:
    while to_visit and pages_saved < MAX_PAGES:
        url, depth = to_visit.pop(0)
        url = normalize_url(url)

        if not url or url in seen or depth > MAX_DEPTH:
            continue

        if not should_follow(url):
            continue

        if not allowed_by_robots(url):
            print(f"Skipping (robots.txt): {url}")
            continue

        headers = {"User-Agent": USER_AGENT}
        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT, allow_redirects=True)
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue

        seen.add(url)
        content_type = resp.headers.get("content-type", "")
        
        if resp.ok:
            if "html" in content_type.lower():
                cleaned_text = extract_clean_text(resp.content)
                save_data = cleaned_text.encode("utf-8")
                filename, saved_path = save_bytes_as_urlname(url, save_data, "text/plain")
            else:
                filename, saved_path = save_bytes_as_urlname(url, resp.content, content_type)    
            
            manifest = {
                "doc_id": hashlib.sha1(url.encode("utf-8")).hexdigest()[:10],
                "source_url": url,
                "retrieved_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "status": resp.status_code,
                "mime_type": content_type,
                "raw_filename": filename,
                "raw_path": saved_path,
                "depth": depth,
                "access_level": "public",
            }
            mf.write(json.dumps(manifest, ensure_ascii=False) + "\n")
            mf.flush()

            pages_saved += 1
            print(f"[{pages_saved}] Saved: {url}")

            # Extract new links (HTML pages only)
            if "html" in content_type.lower():
                soup = BeautifulSoup(resp.content, "html.parser")
                for a in soup.find_all("a", href=True):
                    next_url = normalize_url(urljoin(url, a["href"]))
                    if next_url and next_url not in seen:
                        if should_follow(next_url):
                            to_visit.append((next_url, depth + 1))
        
        time.sleep(DELAY)

print(f"Crawl finished. Total pages saved: {pages_saved}")