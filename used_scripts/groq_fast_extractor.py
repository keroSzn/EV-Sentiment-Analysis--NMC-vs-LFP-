from dotenv import load_dotenv

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

PROMPT_TEMPLATE = """
### ROLE: 
Expert Data Scientist and Electric Vehicle (EV) Analyst.

### TASK:
Analyze the following Reddit post to construct a structured "EV User Profile." 
Extract specific behavioral and environmental features from the text.

### EXTRACTION RULES:
1. *Evidence-Based*: Only extract features if there is explicit or strongly implicit evidence in the text. 
2. *Handle Uncertainty*: If the information is missing or ambiguous, you MUST return "Unknown".
3. *Format*: Return ONLY a valid JSON object. No explanations, no markdown blocks.

### FIELD DEFINITIONS:
- "Battery_type": ["NMC", "LFP", "Unknown"]. (Logic for NMC: High-Performance, Long Range, or Premium trims (e.g., Porsche Taycan, Hyundai Ioniq 5/6, Kia EV6/9, Ford Mach-E, Rivian, or Tesla Long Range/Performance). Also if user mentions "charging only to 80%" to avoid degradation.
Logic for LFP: Standard Range, Entry-level models, or "Blade" batteries (e.g., BYD models, Tesla Model 3/Y RWD, MG, or cheap city commuters). Also if user mentions "charging to 100% daily" as a routine.).
- "Climate": ["Cold", "Mild", "Hot", "Unknown"]. (Look for regional mentions or weather-specific performance feedback).
- "Commute": ["Short", "Long", "Unknown"]. (Short: <30 miles/day or city-only. Long: Highway, inter-state or daily long commutes).
- "Home_Charging": ["Yes", "No", "Unknown"]. (Evidence: 'garage', 'wallbox', 'driveway', 'apartment charging', or 'plugging in at night').
- "Charging_Patience": ["Low", "High", "Unknown"]. (Strictly "Low" if they mention having "no patience", "don't have the patience", hate waiting, or complain about charging times. "High" if they explicitly don't mind waiting or use charging time for breaks. Otherwise "Unknown").
- "Satisfaction": ["Positive", "Neutral", "Negative"]. (Overall sentiment, prioritizing reliability and range/charging experience).

Review to analyze:
"{text}"
"""

def extract_features_llm(text):
    if not isinstance(text, str) or len(text.strip()) < 10:
        return {"Battery_type": "Unknown", "Climate": "Unknown", "Commute": "Unknown", "Home_Charging": "Unknown", "Charging_Patience": "Unknown", "Satisfaction": "Neutral"}
        
    prompt = PROMPT_TEMPLATE.replace("{text}", text.replace('"', '\\"'))
    
    max_retries = 5
    for attempt in range(max_retries):
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.0,
                response_format={"type": "json_object"} 
            )
            
            result_text = chat_completion.choices[0].message.content.strip()
            return json.loads(result_text)
            
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "Rate limit" in error_str:
                wait_time = 10 * (attempt + 1)
                print(f"    Rate limit hit. Waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"Error: {e}")
                break
                
    return {"Battery_type": "Unknown", "Climate": "Unknown", "Commute": "Unknown", "Home_Charging": "Unknown", "Charging_Patience": "Unknown", "Satisfaction": "Neutral"}

def main():
    print("🚀 Starting Fast Groq LLM Feature Extraction...")
    
    input_path = "data5/patience_data.csv"
    output_path = "data5/patience_data_groq_fast.csv"
    
    if not os.path.exists(input_path):
         print(f"Error: {input_path} not found.")
         return
         
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows.")
    
    columns_to_keep = ["URL", "LLM_Battery", "LLM_Climate", "LLM_Commute", "LLM_Home_Charging", "LLM_Patience", "LLM_Satisfaction"]
    
    for col in columns_to_keep[1:]:
        if col not in df.columns:
            df[col] = "Unknown"
            
    if os.path.exists(output_path):
        try:
            existing_df = pd.read_csv(output_path)
            for _, ex_r in existing_df.iterrows():
                if str(ex_r.get('LLM_Satisfaction', 'Unknown')) not in ('Unknown', 'Neutral'):
                    match_idx = df.index[df['URL'] == ex_r['URL']].tolist()
                    if match_idx:
                        for col in columns_to_keep[1:]:
                            if col in existing_df.columns:
                                df.at[match_idx[0], col] = ex_r[col]
            print(f"Existing output file found. Resuming...")
        except:
            pass
            
    processed_count = 0
    total = len(df)
    
    for idx, row in df.iterrows():
        current_sat = str(row.get('LLM_Satisfaction', 'Unknown'))
        if current_sat not in ('Unknown', 'Neutral') and df.at[idx, 'LLM_Satisfaction'] not in ('Unknown', 'Neutral'):
            processed_count += 1
            if processed_count % 50 == 0:
                print(f"[{processed_count}/{total}] Skipped existing...")
            continue
            
        text = str(row.get('Title', '')) + "\n" + str(row.get('Content', ''))
        
        features = extract_features_llm(text)
        
        df.at[idx, 'LLM_Battery'] = features.get('Battery_type', 'Unknown')
        df.at[idx, 'LLM_Climate'] = features.get('Climate', 'Unknown')
        df.at[idx, 'LLM_Commute'] = features.get('Commute', 'Unknown')
        df.at[idx, 'LLM_Home_Charging'] = features.get('Home_Charging', 'Unknown')
        df.at[idx, 'LLM_Patience'] = features.get('Charging_Patience', 'Unknown')
        df.at[idx, 'LLM_Satisfaction'] = features.get('Satisfaction', 'Unknown')
        
        processed_count += 1
        
        if processed_count % 5 == 0:
            print(f"[{processed_count}/{total}] Processed... Savings.")
            # Only save the requested columns
            df[columns_to_keep].to_csv(output_path, index=False)
            
        # VERY SMALL SLEEP for Groq
        time.sleep(1)
        
    df[columns_to_keep].to_csv(output_path, index=False)
    print(f"\n✅ Completed! Saved formatted dataset to: {output_path}")

if __name__ == "__main__":
    main()
