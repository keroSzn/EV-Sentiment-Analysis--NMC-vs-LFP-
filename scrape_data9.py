import requests
import pandas as pd
import time
import datetime
import os

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}

def fetch_reddit_json(query, limit=50):
    print(f"🕵️ Searching for '{query}' across EV subreddits...")
    
    base_url = "https://www.reddit.com/search.json"
    posts = []
    after = None
    
    # Target EV subreddits
    sub_filter = "(subreddit:electricvehicles OR subreddit:evcharging OR subreddit:TeslaModel3 OR subreddit:TeslaModelY OR subreddit:MachE OR subreddit:Ioniq5 OR subreddit:KiaEV6 OR subreddit:BoltEV OR subreddit:Rivian)"
    
    while len(posts) < limit:
        params = {
            'q': f'{query} {sub_filter}',
            'limit': 100,
            'sort': 'relevance',
            'after': after
        }
        
        try:
            response = requests.get(base_url, headers=HEADERS, params=params)
            if response.status_code != 200:
                print(f"⚠️ Error {response.status_code}: {response.text}")
                break
            
            data = response.json()
            items = data.get('data', {}).get('children', [])
            
            if not items:
                break
            
            for item in items:
                post = item['data']
                posts.append({
                    'Title': post.get('title', ''),
                    'Content': post.get('selftext', ''),
                    'Score': post.get('score'),
                    'Upvote_Ratio': post.get('upvote_ratio'),
                    'Num_Comments': post.get('num_comments'),
                    'Created_UTC': datetime.datetime.fromtimestamp(post.get('created_utc', 0)) if post.get('created_utc') else None,
                    'URL': "https://reddit.com" + post.get('permalink', '')
                })
                
            after = data['data']['after']
            if not after:
                break
                
            time.sleep(1.0)
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            break
            
    return posts

def main():
    queries = [
        'don\'t have the patience',
        'have no patience',
        'no patience for level one',
        'no patience for level 1',
        'patience to sit on hold',
        'i certainly don\'t have the patience',
        'patience charging',
        'patience wait'
    ]
    
    data_dir = r'c:\Users\Keramettin\Desktop\projedata\data9'
    os.makedirs(data_dir, exist_ok=True)
    output_path = os.path.join(data_dir, 'scraped_data9.csv')
    
    all_data = []
    seen_urls = set()
    
    print(f"🚀 Starting Scrape for Data9 (Target: 20-30 posts with 'patience')...")

    for q in queries:
        # We only need 20-30 total, so we can fetch a small amount per query
        limit_per_query = 20
        data = fetch_reddit_json(q, limit=limit_per_query)
        
        for post in data:
            url = post['URL']
            if url in seen_urls:
                continue
            
            title = str(post.get('Title', ''))
            content = str(post.get('Content', ''))
            full_text = (title + " " + content).lower()
            
            # Ensure "patience" is actually in the text
            if "patience" not in full_text and "patient" not in full_text:
                continue
                
            # Lower word count threshold as per user request
            if len(full_text.split()) < 20:
                continue
                
            seen_urls.add(url)
            all_data.append(post)
            print(f"✅ Kept post {len(all_data)}: {title[:50]}...")
            
            if len(all_data) >= 40: # Extra safety buffer
                break
        
        if len(all_data) >= 40:
            break
            
        time.sleep(1.0)

    if all_data:
        df = pd.DataFrame(all_data)
        # Final shuffle and selection of top 30
        df = df.sample(frac=1).reset_index(drop=True).head(30)
        df.to_csv(output_path, index=False)
        print(f"\n✅ Saved {len(df)} Reviews to {output_path}")
    else:
        print("❌ No data collected.")

if __name__ == "__main__":
    main()
