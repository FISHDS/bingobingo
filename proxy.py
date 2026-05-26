# Bingo Bingo Local Proxy - run: python proxy.py
# Fetches Taiwan Lottery data server-side (no CORS issues)
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request, json, re, ssl

_SSL_CTX = ssl.create_default_context()
_SSL_CTX.check_hostname = False
_SSL_CTX.verify_mode = ssl.CERT_NONE

PORT = 8765
TIMEOUT = 10

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/json,*/*;q=0.9',
    'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
    'Referer': 'https://www.taiwanlottery.com/',
}

TW_OFFICIAL_API = 'https://api.taiwanlottery.com/TLCAPIWeB/Lottery/LatestBingoResult'

SOURCES = [
    TW_OFFICIAL_API,
    'https://www.taiwanlottery.com/lotto/result/bingo_bingo/',
    'https://www.lotto.mydwpc.com/%E8%B3%93%E6%9E%9Cbingo%E7%9B%B4%E6%92%AD/',
]

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=TIMEOUT, context=_SSL_CTX) as r:
        return r.read().decode('utf-8', errors='replace')

def find_nums_in_obj(obj):
    if isinstance(obj, list):
        nums = [x for x in obj if isinstance(x, int) and 1 <= x <= 80]
        unique = list(dict.fromkeys(nums))
        if len(unique) == 20:
            return unique
        for item in obj:
            r = find_nums_in_obj(item)
            if r: return r
    elif isinstance(obj, dict):
        for k in ('balls','numbers','drawNumbers','ballNumbers','numList','no'):
            if isinstance(obj.get(k), list):
                r = find_nums_in_obj(obj[k])
                if r: return r
        for v in obj.values():
            if isinstance(v, (list, dict)):
                r = find_nums_in_obj(v)
                if r: return r
    return None

def extract_numbers(text):
    # Try JSON
    try:
        nums = find_nums_in_obj(json.loads(text))
        if nums: return nums
    except Exception:
        pass
    # Try __NEXT_DATA__
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>([\s\S]*?)</script>', text)
    if m:
        try:
            nums = find_nums_in_obj(json.loads(m.group(1)))
            if nums: return nums
        except Exception:
            pass
    # Try HTML patterns
    for pat in [
        r'data-(?:ball|num)[^"]*?"\s*(\d{1,2})"',
        r'class="[^"]*ball[^"]*"[^>]*>\s*(\d{1,2})\s*<',
    ]:
        found = [int(x) for x in re.findall(pat, text) if 1 <= int(x) <= 80]
        unique = list(dict.fromkeys(found))
        if len(unique) >= 20:
            return unique[:20]
    return None

def extract_period(text):
    for pat in [
        r'"issueNo"\s*:\s*"(\d{6,})"',
        r'"period"\s*:\s*"(\d{6,})"',
        r'"gameNo"\s*:\s*"(\d{6,})"',
        r'(\d{10,})',
    ]:
        m = re.search(pat, text)
        if m: return m.group(1)
    return None

class ProxyHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # suppress default logging

    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        if self.path == '/ping':
            body = b'{"status":"ok"}'
            self.send_response(200)
            self.send_cors()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(body)
            return

        if self.path.startswith('/latest'):
            result = None
            for src in SOURCES:
                try:
                    print('  trying:', src[:70])
                    text = fetch(src)
                    # Official API: api.taiwanlottery.com/TLCAPIWeB/Lottery/LatestBingoResult
                    try:
                        data = json.loads(text)
                        post = (data.get('content') or {}).get('lotteryBingoLatestPost')
                        if post:
                            raw = post.get('openShowOrder') or post.get('bigShowOrder')
                            if isinstance(raw, list):
                                nums = [int(x) for x in raw if str(x).isdigit() and 1 <= int(x) <= 80]
                            else:
                                nums = None
                            if nums and len(nums) == 20:
                                period = str(post.get('drawTerm', ''))
                                prize = post.get('prizeNum') or {}
                                result = {
                                    'numbers': nums,
                                    'period': period,
                                    'source': src,
                                    'superNum': prize.get('bullEye'),
                                    'bigSmall': prize.get('highLow'),
                                    'oddEven': prize.get('oddEven'),
                                }
                                print('  OK (official API)! period:', period, 'nums:', nums[:5])
                                break
                    except Exception:
                        pass
                    # Fallback: generic HTML/JSON parsing
                    nums = extract_numbers(text)
                    if nums:
                        period = extract_period(text)
                        result = {'numbers': nums, 'period': period, 'source': src}
                        print('  OK (parsed)! period:', period, 'nums:', nums[:5])
                        break
                except Exception as e:
                    print('  failed:', str(e)[:70])

            code = 200 if result else 503
            body = json.dumps(result or {'error': 'all sources failed'}, ensure_ascii=False).encode('utf-8')
            self.send_response(code)
            self.send_cors()
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

if __name__ == '__main__':
    print('=' * 45)
    print('  Bingo Bingo Local Proxy')
    print('  Listening: http://localhost:{}'.format(PORT))
    print('  Data API:  http://localhost:{}/latest'.format(PORT))
    print('  Health:    http://localhost:{}/ping'.format(PORT))
    print('  Press Ctrl+C to stop')
    print('=' * 45)
    HTTPServer(('localhost', PORT), ProxyHandler).serve_forever()
