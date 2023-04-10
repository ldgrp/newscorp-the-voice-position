from tqdm import tqdm
from typing import List
import pandas as pd
import openai
import os

tqdm.pandas()

openai.api_key = os.getenv("OPENAI_API_KEY")

IN_FILE = './data/articles.json'
OUT_FILE = '/data/completions.json'
MODEL = 'text-embedding-ada-002'

def get_embedding(text: str) -> List[float]:
    """Get the embedding for a given text"""
    return openai.Embedding.create(input=[text], model=MODEL)['data'][0]['embedding']

if __name__ == '__main__':
    df = pd.read_json('exports.json')
    df['combined'] = (
        "Title: " + df.title.str.strip() + "; Content: " + df.text.str.strip()
    )

    # Tokenize the text
    df['ada_embedding'] = df.combined.apply(lambda x: get_embedding(x))

    # Cleanup before exporting
    del df['combined']

    # Export as JSON
    df.to_json('exports_embeddings.json', orient='records', indent=2)
