import re
from typing import List

def extract_schema_blocks(markdown: str) -> List[str]:
    return re.findall(r'<script type="application/ld\+json">(.*?)</script>', markdown, re.DOTALL)

def extract_opengraph(markdown: str) -> List[str]:
    return re.findall(r'<meta property="og:[^"]+" content="[^"]+" ?/?>', markdown)

def extract_twitter_cards(markdown: str) -> List[str]:
    return re.findall(r'<meta name="twitter:[^"]+" content="[^"]+" ?/?>', markdown) 