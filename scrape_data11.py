import requests
import pandas as pd
import time
import datetime
import os

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def fetch_reddit_json(query, subreddit, limit=100):
    print(f"Searching for '{query}' in r/{subreddit}...")
    
    base_url = "https://www.reddit.com/search.json"
    posts = []
    after = None
    
    while len(posts) < limit:
        params = {
            'q': f'"{query}" subreddit:{subreddit}',
            'limit': 100,
            'sort': 'relevance',
            'after': after
        }
        
        try:
            response = requests.get(base_url, headers=HEADERS, params=params)
            if response.status_code != 200:
                print(f"Error {response.status_code}: {response.text}")
                break
            
            data = response.json()
            items = data.get('data', {}).get('children', [])
            
            if not items:
                break
            
            for item in items:
                post = item['data']
                posts.append({
                    'Subreddit': subreddit,
                    'Title': post.get('title', ''),
                    'Content': post.get('selftext', ''),
                    'Score': post.get('score'),
                    'Upvote_Ratio': post.get('upvote_ratio'),
                    'Num_Comments': post.get('num_comments'),
                    'Created_UTC': datetime.datetime.fromtimestamp(post.get('created_utc', 0)) if post.get('created_utc') else None,
                    'URL': "https://reddit.com" + post.get('permalink', '')
                })
                
            after = data['data'].get('after')
            if not after:
                break
                
            time.sleep(1.0)
            
        except Exception as e:
            print(f"Exception: {e}")
            break
            
    return posts

def is_question(text):
    text = text.lower().strip()
    if "?" in text: return True
    if text.startswith(("what", "how", "why", "when", "who", "does", "can", "should", "is it")): return True
    if "help" in text and len(text) < 100: return True
    if "advise" in text or "recommendation" in text: return True
    return False

def contains_features(text):
    text = text.lower()
    
    has_climate = any(k in text for k in ['cold', 'winter', 'snow', 'hot', 'summer', 'ac ', 'heater', 'climate'])
    has_commute = any(k in text for k in ['commute', 'daily drive', 'driving to work', 'highway', 'miles a day', 'road trip'])
    has_charging = any(k in text for k in ['home charge', 'home charging', 'garage', 'level 2', 'level 1', 'wallbox', 'apartment', 'plugging in'])
    has_patience = any(k in text for k in ['waiting', 'takes too long', 'patience', 'frustrat', 'slow charge', 'charge speed', 'fast charging', 'annoy'])
    
    return has_climate or has_commute or has_charging or has_patience

def main():
    subreddits = ['teslamotors', 'TeslaModel3', 'TeslaModelY', 'leaf', 'KonaElectric', 'ioniq5', 'BMWI4', 'ChevyBolt', 'F150Lightning', 'Zeekr7xAustralia', 'Zeekr', 'Xpeng','Nio','BYD']
    queries = ['iron phosphate', 'lithium iron', 'blade battery', 'nickel manganese', 'ternary battery', 'standard range', 'long range', 'LFP', 'NMC', 'battery degradation', 'battery health', 'range drop']
    
    data_dir = r'c:\Users\Keramettin\Desktop\projedata\data11'
    output_path = os.path.join(data_dir, 'scraped_data11.csv')
    
    all_data = []
    seen_urls = set()
    
    print(f"Starting Scrape for Data11 (Target: Up to 800 posts matching specific battery terms)...")

    for sub in subreddits:
        for q in queries:
            if len(all_data) >= 800:
                break
                
            data = fetch_reddit_json(q, subreddit=sub, limit=100)
            
            for post in data:
                if len(all_data) >= 800:
                    break
                    
                url = post['URL']
                if url in seen_urls:
                    continue
                    
                title = str(post.get('Title', ''))
                content = str(post.get('Content', ''))
                full_text = title + " " + content
                
                # We skip extremely short posts or purely questions
                if is_question(title):
                    continue
                    
                if len(full_text.split()) < 40:
                    continue
                    
                if not contains_features(full_text):
                    continue
                    
                seen_urls.add(url)
                all_data.append(post)
                safe_title = title[:50].encode('ascii', 'ignore').decode('ascii')
                print(f"Kept post {len(all_data)}: [r/{sub}] {safe_title}...")
                
            time.sleep(1.0)
            
        if len(all_data) >= 800:
            break

    df = pd.DataFrame(all_data)
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} Reviews to {output_path}")

if __name__ == "__main__":
    main()
