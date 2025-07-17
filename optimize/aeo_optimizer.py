import re
from typing import List, Dict

def extract_qa_pairs(markdown: str) -> List[Dict[str, str]]:
    # Simple Q: and A: extraction
    qa_pairs = []
    for match in re.finditer(r'Q: (.*?)\nA: (.*?)(\n|$)', markdown, re.DOTALL):
        qa_pairs.append({'question': match.group(1).strip(), 'answer': match.group(2).strip()})
    return qa_pairs

def extract_faq_clusters(markdown: str) -> List[str]:
    # Find FAQ sections
    faqs = re.findall(r'(?i)faq:?\n(.*?)(\n\n|$)', markdown, re.DOTALL)
    return [faq[0].strip() for faq in faqs]

def extract_conversational_snippets(markdown: str) -> List[str]:
    # Find conversational blocks
    return re.findall(r'"(.*?)"', markdown)

def inject_aeo_blocks(content: str, markdown: str) -> str:
    qa = extract_qa_pairs(markdown)
    faqs = extract_faq_clusters(markdown)
    conv = extract_conversational_snippets(markdown)
    block = f"\n<!-- AEO QA Pairs: {qa} -->\n<!-- AEO FAQ: {faqs} -->\n<!-- AEO Conversational: {conv} -->\n"
    return content + block 