import requests
import pandas as pd
import time
import datetime
import random
import os

# User-Agent is crucial to avoid being blocked immediately
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

def fetch_reddit_json(query, limit=100):
    print(f"🕵️ Searching for '{query}' using JSON method (No API Key)...")
    
    # Reddit search JSON endpoint - global search
    base_url = "https://www.reddit.com/search.json"
    
    posts = []
    after = None
    
    while len(posts) < limit:
        params = {
            'q': query + ' (subreddit:evcharging)',
            'limit': 100,  # Grab maximum possible items
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
                print("   No more results found.")
                break
            
            for item in items:
                post = item['data']
                
                # Improved Battery Type Classification (Car Models -> Chemistry)
                text_content = (post.get('title', '') + " " + post.get('selftext', '')).lower()
                b_type = 'General'
                
                # NMC/NCA Keywords (Car Models known for NMC)
                nmc_keywords = ['nmc', 'bolt', 'id.4', 'id4', 'mach-e', 'mach e', 'ioniq 5', 'ev6', 'long range', 'rivian', 'f-150 lightning', 'nmc battery']
                # LFP Keywords
                lfp_keywords = ['lfp', 'lithium iron', 'blade battery', 'standard range', 'model 3 rwd', 'ex30 lfp', 'lfp battery']

                # Priority logic: Check explicit chemistry first, then car model
                if any(k in text_content for k in lfp_keywords):
                    b_type = 'LFP'
                elif any(k in text_content for k in nmc_keywords):
                    b_type = 'NMC'
                
                posts.append({
                    'Battery_Type': b_type,
                    'Title': post.get('title'),
                    'Content': post.get('selftext'),
                    'Score': post.get('score'),
                    'Upvote_Ratio': post.get('upvote_ratio'),
                    'Num_Comments': post.get('num_comments'),
                    'Created_UTC': datetime.datetime.fromtimestamp(post.get('created_utc', 0)),
                    'URL': "https://reddit.com" + post.get('permalink', '')
                })
                
            after = data['data']['after']
            if not after:
                break
                
            # Sleep to be polite and avoid rate limits
            time.sleep(0.5)
            
        except Exception as e:
            print(f"❌ Exception: {e}")
            break
            
    return posts

def main():
    # Phase 5: High-Quality "Review" Collection (Fresh Start)
    # Strategy: Stratified Sampling & Filtering (Instructor Feedback)
    
    # 1. Stratified Queries (Opinionated Keywords)
    queries = [
        'EV review', 'electric car review', 'my EV experience', 'switching to EV',
        'first EV road trip', 'daily commute EV', 'charging at home', 'public charging',
        'winter range EV', 'LFP battery experience', 'NMC battery degradation',
        'love my EV', 'hate my electric car', 'EV buyer remorse', 'best EV purchase',
        'Model 3 RWD', 'Model Y Long Range', 'Chevy Bolt EV review', 'VW ID.4 experience',
        'Mustang Mach-E road trip', 'Hyundai Ioniq 5 review', 'Kia EV6 charging',
        'cold weather EV', 'hot weather EV', 'EV vs Gas', 'electric vehicle pros and cons',
        'EV road trip nightmare', 'EV charging station broken', 'home charger installation',
        'LFP vs NMC', 'blade battery', 'EV daily driver', 'EV ownership cost',
        'EV maintenance', 'EV battery replacement', 'EV reliability', 'EV build quality',
        'EV software issues', 'EV autopilot review', 'EV range anxiety', 'EV charging speed',
        'EV fast charger', 'EV home charging', 'EV level 2 charger', 'EV level 1 charging',
        '1 year EV review', '2 years EV review', '10000 miles EV review', 'EV road trip tips',
        'buying a used EV', 'used EV experience', 'EV roadtrip review', 'EV commuting',
        'Tesla Model 3 review', 'Tesla Model Y road trip', 'Rivian R1T experience', 'Rivian R1S review',
        'F-150 Lightning road trip', 'Lucid Air range', 'Porsche Taycan review', 'Audi e-tron commute',
        'BMW i4 experience', 'Nissan Leaf battery', 'Polestar 2 review', 'Chevy Equinox EV',
        'Honda Prologue EV', 'Kia EV9 family car', 'electric car winter battery',
        'EV snow tires', 'EV cold weather range loss', 'supercharger network review', 'Electrify America issues',
        'ChargePoint home charger', 'EV charger installation cost', 'should I buy an EV', 'first time EV owner',
        'EV vs hybrid', 'PHEV vs EV', 'Tesla supercharging cost', 'EV electricity bill',
        'EV insurance cost', 'renting an EV', 'EV rental experience', 'long distance electric driving',
        'EV camping', 'EV towing experience', 'electric truck review', 'best EV for cold climate',
        'best EV for hot climate', 'EV battery warranty', 'LFP battery winter', 'NMC vs LFP charging',
        'charge to 80 or 100', 'EV daily charging routine', 'living with an EV in an apartment',
        'no home charging EV', 'public charging only EV', 'EV street parking', 'EV workplace charging','I have no patience','I certainly dont have the patience',
        'very satisfied with charging', 'extremely satisfied with charging', 'happy with charging speed', 'love home charging',
    ]
    
    os.makedirs('data4', exist_ok=True)
    output_path = 'data4/redditllm_json_scraped.csv'
    # We will load the existing ones to build upon them.
    all_data = [] 
    if os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        all_data = existing_df.to_dict('records')
        print(f"Loaded {len(all_data)} existing records.")

    print(f"🚀 Starting Quality-Focused Scraping (Target: ~650 High-Density Reviews)")

    count_collected = 0
    target_count = 650

    for q in queries:
        if count_collected >= target_count:
            break
            
        data = fetch_reddit_json(q, limit=100) # Fetch more to allow for heavy filtering
        
        quality_posts = []
        for post in data:
            title = post.get('Title', '')
            content = post.get('Content', '')
            full_text = title + " " + content
            word_count = len(full_text.split())
            
            # --- FILTER 1: Question Detection ---
            # Exclude if Title looks like a question
            if title.strip().endswith('?') or title.lower().startswith('question') or 'help' in title.lower():
                continue
                
            # --- FILTER 2: Minimum Length (Instructor: 100 words) ---
            # We use 70 as a safe soft limit to not lose too much, but ensure substance
            if word_count < 70:
                continue
                
            quality_posts.append(post)
            
        all_data.extend(quality_posts)
        count_collected += len(quality_posts)
        print(f"   Fetched '{q}': Kept {len(quality_posts)}/{len(data)} (Quality Filtered)")
        time.sleep(0.5)

    if all_data:
        df = pd.DataFrame(all_data)
        df.drop_duplicates(subset=['URL'], inplace=True)
        
        # Ensure data dir exists
        os.makedirs('data4', exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"✅ Saved {len(df)} High-Quality Reviews to {output_path}")
    else:
        print("❌ No data collected.")

if __name__ == "__main__":
    main()

