import re
from typing import Dict, List, Optional


def classify_intent(query: str) -> str:
    q = query.lower().strip()

    if re.search(r"\b(where\s+(was|is|did)|when\s+(did|was)|timestamp|which\s+part|kab\s+bola)\b", q):
        return "where-discussed"

    if re.search(r"\b(summar(y|ise|ize)|recap|till\s+now|so\s+far|kya\s+padha)\b", q):
        return "summarise-so-far"

    if re.search(r"\b(quiz|test\s+me|ask\s+me\s+a\s+question)\b", q):
        return "quiz"

    if re.search(r"\b(compare|difference\s+between|vs\.?|versus)\b", q):
        return "compare"

    if re.search(r"\b(slide|pdf|document|page|doc)\b", q):
        return "doc-lookup"

    return "explain"
