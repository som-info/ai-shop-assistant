"""Tiny TF-IDF retriever over product text (pure Python, no heavy deps)."""
import math
import re
from collections import Counter

from .i18n import FA_GLOSSARY, normalize_fa

_TOKEN = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)?|[\u0600-\u06FF\u200c]+")
STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "to", "of", "in", "on", "at", "is", "are", "i", "me", "my",
    "you", "your", "do", "does", "have", "has", "need", "want", "looking", "something", "some", "any",
    "recommend", "suggest", "please", "can", "could", "what", "which", "good", "best", "buy", "show", "find",
    "it", "that", "this", "be", "by", "from", "up", "about", "under", "below", "less", "than",
    "یک", "برای", "به", "از", "که", "را", "با", "و", "در", "می‌خواهم", "میخواهم", "میخوام", "می‌خوام",
    "پیشنهاد", "بده", "بدهید", "دارید", "دارین", "چه", "چی", "خوب", "لطفا", "لطفاً", "یه", "من", "کنید",
}


def tokenize(text: str) -> list[str]:
    text = normalize_fa(text.lower())
    out = []
    for tok in _TOKEN.findall(text):
        if tok in STOPWORDS:
            continue
        mapped = FA_GLOSSARY.get(tok)
        if mapped:
            out.extend(mapped.split())
        out.append(tok)
        if tok.endswith("s") and len(tok) > 3:  # naive singular form
            out.append(tok[:-1])
    return out


class TfidfIndex:
    def __init__(self, docs: dict[str, str]):
        self.ids = list(docs)
        tokenized = {k: tokenize(v) for k, v in docs.items()}
        n = len(docs) or 1
        df = Counter(tok for toks in tokenized.values() for tok in set(toks))
        self.idf = {tok: math.log((1 + n) / (1 + c)) + 1 for tok, c in df.items()}
        self.vectors = {}
        for key, toks in tokenized.items():
            tf = Counter(toks)
            vec = {tok: (cnt / len(toks)) * self.idf[tok] for tok, cnt in tf.items()} if toks else {}
            norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
            self.vectors[key] = {k: v / norm for k, v in vec.items()}

    def search(self, query: str, k: int = 5) -> list[tuple[str, float]]:
        q = Counter(tokenize(query))
        if not q:
            return []
        qvec = {tok: cnt * self.idf.get(tok, 0.0) for tok, cnt in q.items()}
        scores = []
        for key, vec in self.vectors.items():
            s = sum(w * vec.get(tok, 0.0) for tok, w in qvec.items())
            if s > 0:
                scores.append((key, s))
        scores.sort(key=lambda x: (-x[1], x[0]))
        return scores[:k]


def product_document(p) -> str:
    return " ".join([p.name, p.name_fa, p.category, p.category, p.tags, p.tags, p.description])
