from tqdm import tqdm
import pandas as pd
import openai
import os
import re

tqdm.pandas()

openai.api_key = os.getenv("OPENAI_API_KEY")

IN_FILE = './data/articles.json'
OUT_FILE = './data/articles_with_completions_v3.json'
MODEL = 'gpt-3.5-turbo'

PROMPT = "You are a rating system performing semantic analysis of text.\nUse your knowledge of Australian politics, politicians, journalists, and their possible political bias when analysing the text.\nYou will output a single integer with some possible explanation.\nYou MUST:\nOutput 0 if the text is not related to the Voice to parliament referendum.\nOutput from 1-10 the degree to which the text makes a stance in the Voice to parliament referendum. Specifically 1 means the article is strongly critical of the referendum, 5 is neutral, and 10 is a strongly in favour of the referendum.\n Print the score first followed by a dash and then the explanation."

def get_completion(text: str) -> str:
    return openai.ChatCompletion.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": text}
        ],
        temperature=0,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=["\n"]
    )['choices'][0]['message']['content'].strip()

def extract_score(text: str) -> int:
    maybe_score = re.search(r'\d+', text)
    if maybe_score is None:
        return -1
    return int(maybe_score.group(0))

if __name__ == '__main__':
    # Import the data
    print('Loading data...')
    df = pd.read_json(IN_FILE)

    df['combined'] = (
        "Title: " + df.title.str.strip() + "; Content: " + df.text.str.strip()
    )

    # Complete the text with the model
    print('Getting completions...')
    df['completion'] = df.combined.progress_apply(lambda x: get_completion(x))
    print('Extracting score...')
    df['score'] = df.completion.progress_apply(lambda x: extract_score(x))
    
    # Cleanup before exporting
    del df['combined']

    # Export as JSON
    print('Exporting as JSON...')
    df.to_json(OUT_FILE, orient='records', indent=2)