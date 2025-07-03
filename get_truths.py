import cloudscraper
import json
import re
import os
from datetime import datetime
import time
import random

# --- Import libraries for plotting ---
try:
    import matplotlib.pyplot as plt
    from collections import Counter
    import calendar
except ImportError:
    print("Matplotlib or collections not found. Please run 'pip install matplotlib' to use the trend analysis feature.")
    plt = None # Set to None so we can check for it later

# --- Import Pillow for ASCII Art ---
try:
    from PIL import Image
except ImportError:
    print("Pillow library not found. Please run 'pip install Pillow' to display ASCII art.")
    Image = None

# --- Constants for colored terminal output ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    DIM = '\033[2m'

# --- List of User-Agents to rotate through ---
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
]

# --- ASCII Art Generation ---
def rgb_to_ansi(r, g, b):
    if r == g and g == b:
        if r < 8: return 16
        if r > 248: return 231
        return round(((r - 8) / 247) * 24) + 232
    return 16 + (36 * round(r / 255 * 5)) + (6 * round(g / 255 * 5)) + round(b / 255 * 5)
def display_ascii_art():
    if not Image: return
    IMAGE_PATH, MAX_WIDTH = "trump_blocky.png", 50
    if not os.path.exists(IMAGE_PATH): return
    CACHE_PATH = f"ascii_art_halfblock_w{MAX_WIDTH}.txt"
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, 'r', encoding='utf-8') as f: print(f.read())
            return
        except Exception: pass
    print(f"{Colors.DIM}Generating high-detail art (w={MAX_WIDTH}) for the first time...{Colors.ENDC}")
    try:
        img = Image.open(IMAGE_PATH)
        width, height = img.size
        new_height = int((height / width) * MAX_WIDTH * 0.9)
        if new_height % 2 != 0: new_height -= 1
        resized_img = img.resize((MAX_WIDTH, new_height), resample=Image.Resampling.LANCZOS).convert("RGB")
        ascii_lines = []
        for y in range(0, new_height, 2):
            line = ""
            for x in range(MAX_WIDTH):
                r1, g1, b1 = resized_img.getpixel((x, y))
                r2, g2, b2 = resized_img.getpixel((x, y + 1))
                line += f"\033[38;5;{rgb_to_ansi(r1, g1, b1)}m\033[48;5;{rgb_to_ansi(r2, g2, b2)}m▀"
            ascii_lines.append(line + Colors.ENDC)
        full_art = "\n".join(ascii_lines)
        with open(CACHE_PATH, "w", encoding='utf-8') as f: f.write(full_art)
        print(full_art)
    except Exception as e: print(f"{Colors.FAIL}Could not generate ASCII art: {e}{Colors.ENDC}")

# --- Core Data Processing ---
def process_and_save_data(raw_posts, mode='overwrite'):
    if not raw_posts:
        print(f"{Colors.WARNING}No new posts to process.{Colors.ENDC}")
        return
    print(f"{Colors.OKCYAN}Processing {len(raw_posts)} posts...{Colors.ENDC}")
    lean_posts = [{
        "id": p.get("id"), "created_at": p.get("created_at"), "url": p.get("url"),
        "content": strip_html(p.get("content", "")), "username": p.get("account", {}).get("username"),
        "media_urls": [m.get('url') for m in p.get('media_attachments', [])],
        "card": {"title": p.get("card", {}).get("title"), "url": p.get("card", {}).get("url")} if p.get("card") else None,
        "replies_count": p.get("replies_count"), "reblogs_count": p.get("reblogs_count"), "favourites_count": p.get("favourites_count"),
    } for p in raw_posts]
    update_stats_history(raw_posts)
    final_data = lean_posts
    try:
        with open("truths.json", 'r') as f: existing_data = json.load(f)
        if mode == 'append':
            existing_ids = {p['id'] for p in existing_data}
            unique_new_posts = [p for p in lean_posts if p['id'] not in existing_ids]
            final_data = existing_data + unique_new_posts
            print(f"Appended {len(unique_new_posts)} unique posts.")
        elif mode == 'prepend':
            existing_ids = {p['id'] for p in existing_data}
            unique_new_posts = [p for p in lean_posts if p['id'] not in existing_ids]
            final_data = unique_new_posts + existing_data
            print(f"Prepended {len(unique_new_posts)} new posts.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("No existing truths.json found, creating a new one.")
    with open("truths.json", "w") as f: json.dump(final_data, f, indent=2)
    print(f"{Colors.OKGREEN}✔ truths.json updated. Total posts: {len(final_data)}.{Colors.ENDC}")

def update_stats_history(raw_posts):
    try:
        with open("stats_history.json", 'r') as f: history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): history = {"account_history": []}
    timestamp = datetime.now().isoformat()
    account_stats = raw_posts[0].get("account", {})
    history["account_history"].append({
        "timestamp": timestamp, "followers_count": account_stats.get("followers_count"), "statuses_count": account_stats.get("statuses_count")
    })
    with open("stats_history.json", "w") as f: json.dump(history, f, indent=2)
    print(f"{Colors.OKCYAN}✔ Stat history updated.{Colors.ENDC}")

# --- Fetching Logic ---
def fetch_posts(scraper, url, get_headers=False):
    scraper.headers['User-Agent'] = random.choice(USER_AGENTS)
    time.sleep(random.uniform(0.5, 1.5))
    print(f"{Colors.DIM}Fetching {url}...{Colors.ENDC}")
    response = scraper.get(url)
    if get_headers:
        return response
    if response.status_code == 429:
        print(f"{Colors.FAIL}❌ Received HTTP 429: Too Many Requests. The server is rate-limiting us.{Colors.ENDC}")
        print(f"{Colors.WARNING}Taking a 30-second break...{Colors.ENDC}")
        time.sleep(30)
        response = scraper.get(url)
    return response.json() if response.status_code == 200 else None

def smart_update():
    scraper = cloudscraper.create_scraper()
    print(f"{Colors.OKCYAN}Checking for new posts since last session...{Colors.ENDC}")
    latest_local_id = None
    try:
        with open("truths.json", 'r') as f: local_posts = json.load(f)
        if local_posts: latest_local_id = local_posts[0]['id']
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"{Colors.WARNING}No local data found. Fetching latest posts for a fresh start.{Colors.ENDC}")
        fetch_and_overwrite_latest()
        return
    if not latest_local_id:
        print(f"{Colors.WARNING}Local data is empty. Fetching latest posts.{Colors.ENDC}")
        fetch_and_overwrite_latest()
        return
    ACCOUNT_ID = "107780257626128497"
    api_url = f"https://truthsocial.com/api/v1/accounts/{ACCOUNT_ID}/statuses?since_id={latest_local_id}"
    new_data = fetch_posts(scraper, api_url)
    if new_data:
        print(f"{Colors.OKGREEN}Found {len(new_data)} new post(s)!{Colors.ENDC}")
        process_and_save_data(new_data, mode='prepend')
    else:
        print(f"{Colors.OKGREEN}You are already up-to-date.{Colors.ENDC}")

def fetch_and_overwrite_latest():
    scraper = cloudscraper.create_scraper()
    ACCOUNT_ID = "107780257626128497"
    api_url = f"https://truthsocial.com/api/v1/accounts/{ACCOUNT_ID}/statuses?exclude_replies=true&limit=40"
    data = fetch_posts(scraper, api_url)
    if data: process_and_save_data(data, mode='overwrite')

def fetch_more_posts():
    scraper = cloudscraper.create_scraper()
    oldest_local_id = None
    try:
        with open("truths.json", 'r') as f: local_posts = json.load(f)
        if local_posts: oldest_local_id = local_posts[-1]['id']
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"{Colors.FAIL}Local data file not found. Cannot fetch more.{Colors.ENDC}")
        return
    if not oldest_local_id:
        print(f"{Colors.WARNING}No posts found to paginate from. Fetch latest first.{Colors.ENDC}")
        return
    ACCOUNT_ID = "107780257626128497"
    api_url = f"https://truthsocial.com/api/v1/accounts/{ACCOUNT_ID}/statuses?exclude_replies=true&limit=40&max_id={oldest_local_id}"
    data = fetch_posts(scraper, api_url)
    if data: process_and_save_data(data, mode='append')

# --- UI and Display Logic ---
def strip_html(text): return re.sub('<[^<]+?>', '', text)
def display_post(post):
    print(f"{Colors.DIM}--------------------------------------------------{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.OKCYAN}{post.get('username')}{Colors.ENDC}")
    print(f"{Colors.DIM}Posted on: {post.get('created_at')}{Colors.ENDC}")
    if post.get('content'): print(f"\n{Colors.WARNING}Content:{Colors.ENDC}\n{post.get('content')}")
    if post.get('media_urls'):
        print(f"\n{Colors.WARNING}Media:{Colors.ENDC}")
        for url in post.get('media_urls'): print(f"  - {Colors.OKBLUE}{url}{Colors.ENDC}")
    card = post.get('card')
    if card and card.get('url'):
        print(f"\n{Colors.WARNING}Shared Link:{Colors.ENDC}")
        print(f"  Title: {card.get('title')}\n  Link: {Colors.OKBLUE}{card.get('url')}{Colors.ENDC}")
    print(f"\n{Colors.DIM}Stats: {post.get('reblogs_count')} ReTruths, {post.get('favourites_count')} Likes{Colors.ENDC}")
    print(f"Original Post: {Colors.UNDERLINE}{Colors.OKBLUE}{post.get('url')}{Colors.ENDC}")
def search_posts():
    if not os.path.exists('truths.json'): return
    query = input(f"Enter search query: ").strip().lower()
    if not query: return
    with open('truths.json', 'r') as f: posts = json.load(f)
    found_posts = [p for p in posts if query in json.dumps(p).lower()]
    print(f"\n{Colors.OKGREEN}--- Found {len(found_posts)} Matching Posts ---{Colors.ENDC}")
    for post in found_posts: display_post(post)
def show_stats_and_records():
    print(f"\n{Colors.HEADER}--- Overall Stats & Records ---{Colors.ENDC}")
    try:
        with open('stats_history.json', 'r') as f: history = json.load(f)
        acc_history = history.get('account_history', [])
        if acc_history:
            max_followers_record = max(acc_history, key=lambda x: x.get('followers_count', 0))
            ts = max_followers_record['timestamp'][:19].replace("T", " ")
            count = max_followers_record['followers_count']
            print(f"\n{Colors.BOLD}Highest Recorded Followers:{Colors.ENDC}")
            print(f"  {Colors.OKCYAN}{count:,}{Colors.ENDC} on {ts}")
    except (FileNotFoundError, json.JSONDecodeError): print(f"\n{Colors.WARNING}Could not find follower history.{Colors.ENDC}")
    try:
        with open('truths.json', 'r') as f: posts = json.load(f)
        if not posts:
            print(f"\n{Colors.WARNING}No posts in truths.json to analyze.{Colors.ENDC}")
            return
        most_replies = max(posts, key=lambda x: x.get('replies_count', 0))
        most_reblogs = max(posts, key=lambda x: x.get('reblogs_count', 0))
        most_favourites = max(posts, key=lambda x: x.get('favourites_count', 0))
        def print_record(label, post, key):
            content_snippet = (post.get('content') or "No Content")[:50] + "..."
            print(f"\n{Colors.BOLD}{label}:{Colors.ENDC}")
            print(f"  {Colors.OKCYAN}{post.get(key):,}{Colors.ENDC} - \"{content_snippet}\" on {post.get('created_at')[:10]}")
        print_record("Most Replies", most_replies, "replies_count")
        print_record("Most ReTruths", most_reblogs, "reblogs_count")
        print_record("Most Favourites", most_favourites, "favourites_count")
    except (FileNotFoundError, json.JSONDecodeError): print(f"\n{Colors.WARNING}Could not find posts to analyze in truths.json.{Colors.ENDC}")

def analyze_posting_trends():
    if not plt:
        print(f"{Colors.FAIL}Matplotlib library not found. Cannot generate graph.{Colors.ENDC}\nPlease run 'pip install matplotlib' to use this feature.{Colors.ENDC}")
        return
    print(f"\n{Colors.HEADER}--- Analyzing Posting Trends ---{Colors.ENDC}")
    try:
        with open('truths.json', 'r') as f: posts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"{Colors.FAIL}No post data found. Fetch some posts first.{Colors.ENDC}")
        return
    if not posts:
        print(f"{Colors.WARNING}Your truths.json file is empty.{Colors.ENDC}")
        return
    monthly_counts = Counter(p.get('created_at', '')[:7] for p in posts if p.get('created_at'))
    if not monthly_counts:
        print(f"{Colors.FAIL}Could not find any valid dates in the posts.{Colors.ENDC}")
        return
    sorted_months = sorted(monthly_counts.keys())
    counts = [monthly_counts[month] for month in sorted_months]
    month_labels = [f"{calendar.month_abbr[int(m.split('-')[1])]}\n{m.split('-')[0]}" for m in sorted_months]
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.bar(month_labels, counts, color='#2a9d8f')
    ax.set_title("Monthly Posting Frequency", fontsize=16)
    ax.set_ylabel("Number of Posts", fontsize=12)
    ax.set_xlabel("Month", fontsize=12)
    for i, count in enumerate(counts):
        ax.text(i, count + (max(counts) * 0.01), str(count), ha='center', color='black')
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    print(f"{Colors.OKGREEN}Displaying post frequency graph... Close the graph window to return to the menu.{Colors.ENDC}")
    plt.show()

def check_connection_status():
    scraper = cloudscraper.create_scraper()
    print(f"\n{Colors.OKCYAN}Pinging API to check status...{Colors.ENDC}")
    ACCOUNT_ID = "107780257626128497"
    api_url = f"https://truthsocial.com/api/v1/accounts/{ACCOUNT_ID}/statuses?limit=1"
    try:
        response = fetch_posts(scraper, api_url, get_headers=True)
        code = response.status_code
        if code == 200: print(f"{Colors.OKGREEN}✔ Status: {code} OK - Connection is working perfectly.{Colors.ENDC}")
        elif code == 403: print(f"{Colors.FAIL}❌ Status: {code} Forbidden - We are likely being blocked by Cloudflare.{Colors.ENDC}")
        elif code == 404: print(f"{Colors.FAIL}❌ Status: {code} Not Found - The API endpoint may have changed.{Colors.ENDC}")
        elif str(code).startswith('5'): print(f"{Colors.FAIL}❌ Status: {code} Server Error - Truth Social's servers are having issues.{Colors.ENDC}")
        else: print(f"{Colors.WARNING}❓ Status: {code} - An unexpected response was received.{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}❌ A network error occurred. Check your internet connection.{Colors.ENDC}")
        print(f"{Colors.DIM}{e}{Colors.ENDC}")

def show_new_posts_since_last_check():
    if not os.path.exists('truths.json'):
        print(f"{Colors.WARNING}No local post data found. Fetch some posts first.{Colors.ENDC}")
        return
    try:
        with open('truths.json', 'r') as f:
            posts = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        print(f"{Colors.WARNING}Could not read truths.json.{Colors.ENDC}")
        return
    if not posts:
        print(f"{Colors.WARNING}No posts found in truths.json.{Colors.ENDC}")
        return

    # Track last check timestamp in a file
    last_check_file = ".last_check"
    last_check_time = None
    if os.path.exists(last_check_file):
        with open(last_check_file, 'r') as f:
            last_check_time = f.read().strip()
    # If never checked before, show nothing
    if not last_check_time:
        print(f"{Colors.OKCYAN}No previous check found. All posts are considered old.{Colors.ENDC}")
        with open(last_check_file, 'w') as f:
            f.write(datetime.now().isoformat())
        return

    # Find new posts since last check
    new_posts = [p for p in posts if p.get("created_at", "") > last_check_time]
    if not new_posts:
        print(f"{Colors.OKCYAN}No new posts since your last check!{Colors.ENDC}")
    else:
        if len(new_posts) > 10:
            print(f"{Colors.WARNING}There are {len(new_posts)} new posts since your last check.{Colors.ENDC}")
            confirm = input("Show all new posts? (y/N): ").strip().lower()
            if confirm != 'y':
                print(f"{Colors.DIM}Returning to main menu...{Colors.ENDC}")
                with open(last_check_file, 'w') as f:
                    f.write(datetime.now().isoformat())
                return
        print(f"{Colors.OKGREEN}Showing {len(new_posts)} new post(s) since your last check:{Colors.ENDC}")
        # Show from oldest to newest
        for post in sorted(new_posts, key=lambda p: p.get("created_at", "")):
            display_post(post)
    # Update last check time
    with open(last_check_file, 'w') as f:
        f.write(datetime.now().isoformat())

def main_menu():
    display_ascii_art()
    smart_update()
    while True:
        print(f"\n{Colors.HEADER}--- Main Menu ---{Colors.ENDC}")
        print("1. Search Posts")
        print(f"2. Fetch More Posts {Colors.DIM}(Go Back in Time){Colors.ENDC}")
        print(f"3. Refresh & Overwrite All {Colors.DIM}(Start Fresh){Colors.ENDC}")
        print("4. View Overall Stats & Records")
        print("5. Analyze Posting Trends")
        print("6. Check Connection Status")
        print("7. Show New Posts Since Last Check")
        print("8. Exit")
        choice = input("> ").strip()
        if choice == '1': search_posts()
        elif choice == '2': fetch_more_posts()
        elif choice == '3': fetch_and_overwrite_latest()
        elif choice == '4': show_stats_and_records()
        elif choice == '5': analyze_posting_trends()
        elif choice == '6': check_connection_status()
        elif choice == '7': show_new_posts_since_last_check()
        elif choice == '8': break
        else: print(f"{Colors.FAIL}Invalid choice.{Colors.ENDC}")

if __name__ == "__main__":
    main_menu()
