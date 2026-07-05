import pandas as pd
import os
import glob
from transformers import pipeline
import torch
import time

def log(msg):
    print(msg, flush=True)

log("Loading RoBERTa model...")
model_path = os.path.abspath("scripts/model_cache")

device = 0 if torch.cuda.is_available() else -1
log(f"Using device: {'GPU' if device == 0 else 'CPU'}")

try:
    # Load model weights locally and fetch tokenizer (small files) online
    sentiment_task = pipeline("sentiment-analysis", 
                              model=model_path, 
                              tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest",
                              device=device)
except Exception as e:
    log(f"Error loading model: {e}")
    log("Trying full online fallback...")
    sentiment_task = pipeline("sentiment-analysis", 
                              model="cardiffnlp/twitter-roberta-base-sentiment-latest", 
                              tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest",
                              device=-1)

def get_roberta_sentiment(text, threshold=0.70):
    if not isinstance(text, str) or not text.strip(): 
        return None
    text = text[:1500] 
    try:
        results = sentiment_task(text, top_k=None)
        max_label = results[0]['label'].lower()
        max_score = results[0]['score']
        
        if max_score < threshold:
            return None  # Return None so it falls back to the original LLM satisfaction label
        elif 'positive' in max_label:
            return 'Positive'
        elif 'negative' in max_label:
            return 'Negative'
        else:
            return 'Neutral'
    except Exception as e:
        log(f"Error in get_roberta_sentiment: {e}")
        return None

log("Scanning all folders and building URL matching table...")
lookup = {}
all_csvs = glob.glob('**/*.csv', recursive=True)

for f in all_csvs:
    if 'scraped' in f.lower() or 'independent' in f.lower() or 'roberta' in f.lower() or 'final' in f.lower(): 
        if f != 'reddit_training_data_before_final.csv':
            continue
    try:
        df_temp = pd.read_csv(f)
        cols = list(df_temp.columns)
        if 'URL' in cols and 'LLM_Model' in cols:
            for _, row in df_temp.iterrows():
                key = tuple(str(row[c]).strip().lower() for c in ['LLM_Model', 'LLM_Battery', 'LLM_Climate', 'LLM_Commute', 'LLM_Home_Charging', 'LLM_Patience'])
                lookup[key] = str(row['URL']).strip()
    except: 
        pass

log(f"Lookup table ready: {len(lookup)} unique records found.")

log("Loading raw texts (scraped files)...")
url_to_text = {}
scraped_files = glob.glob('**/scraped_*.csv', recursive=True) + glob.glob('**/*json_scraped.csv', recursive=True)
for f in scraped_files:
    try:
        s = pd.read_csv(f)
        if 'URL' in s.columns and 'Title' in s.columns:
            s['Full_Text'] = s['Title'].fillna('') + ' ' + s['Content'].fillna('')
            for _, row in s.iterrows():
                url_to_text[str(row['URL']).strip()] = row['Full_Text']
    except: 
        pass

log(f"Text pool ready: {len(url_to_text)} post texts loaded.")

target = pd.read_csv('reddit_training_data_before_final.csv')
log(f"\nProcessing target file ({len(target)} rows)...")

results = []
matched_url = 0
roberta_done = 0
start_time = time.time()

for idx, row in target.iterrows():
    if idx > 0 and idx % 50 == 0:
        elapsed = time.time() - start_time
        avg_time = elapsed / idx
        remaining = avg_time * (len(target) - idx)
        log(f"Progress: {idx}/{len(target)} | Match Rate: {matched_url}/{idx} | ETA: {remaining/60:.1f} min")
        
    key = tuple(str(row[c]).strip().lower() for c in ['LLM_Model', 'LLM_Battery', 'LLM_Climate', 'LLM_Commute', 'LLM_Home_Charging', 'LLM_Patience'])
    
    url = lookup.get(key)
    sentiment = row['LLM_Satisfaction'] 
    
    if url:
        matched_url += 1
        text = url_to_text.get(url)
        if text:
            roberta_sentiment = get_roberta_sentiment(text, threshold=0.70)
            if roberta_sentiment is not None:
                sentiment = roberta_sentiment
                roberta_done += 1
            
    row_data = row.to_dict()
    row_data['LLM_Satisfaction'] = sentiment
    results.append(row_data)

final_df = pd.DataFrame(results)
output_file = 'reddit_training_data_roberta_final.csv'
final_df.to_csv(output_file, index=False)

log(f"\nPROCESSING COMPLETED!")
log(f"Matched URLs : {matched_url}")
log(f"RoBERTa Analysis : {roberta_done}")
log(f"Saved To : {output_file}")
log("\nNew Class Distribution:")
log(str(final_df['LLM_Satisfaction'].value_counts()))
