"""Extractive keywords for abstracts, scored by TF-IDF against the corpus."""

from __future__ import annotations

import math
import re
from collections import Counter

STOPWORDS = frozenset("""
a about above after again against all also although among an and any are as at be because been
before being below between both but by can could did do does doing down during each either et few
for from further had has have having here how however i if in into is it its itself just less like
made make many may more most much must new no nor not novel now of on once one only or other our
ours out over own paper per propose proposed proposes present presents provide same several should
show shows since so some such than that the their them then there these they this those through
thus to too two under until up upon us use used uses using via was we well were what when where
whether which while who whom why will with within without would yet you your al based approach
approaches method methods results result work works study first however significantly furthermore
moreover existing different various achieve achieves achieved demonstrate demonstrates task tasks
""".split())

TOKEN = re.compile(r"[a-z][a-z0-9\-]+")


def tokenize(text: str) -> list[str]:
    return [t.strip("-") for t in TOKEN.findall(text.lower()) if t.strip("-")]


def candidate_terms(text: str) -> list[str]:
    """Unigrams and bigrams that neither start nor end with a stopword."""
    tokens = tokenize(text)
    terms = [t for t in tokens if t not in STOPWORDS and len(t) > 2]
    terms += [f"{a} {b}" for a, b in zip(tokens, tokens[1:])
              if a not in STOPWORDS and b not in STOPWORDS and len(a) > 2 and len(b) > 2]
    return terms


class KeywordExtractor:
    def __init__(self, corpus: list[str]):
        self.n_docs = len(corpus)
        self.doc_freq = Counter(term for doc in corpus for term in set(candidate_terms(doc)))

    def idf(self, term: str) -> float:
        return math.log((1 + self.n_docs) / (1 + self.doc_freq[term])) + 1

    def extract(self, text: str, k: int = 6) -> list[str]:
        counts = Counter(candidate_terms(text))
        # A bigram counts as a phrase only if it repeats in the text or occurs in another
        # document; otherwise accidental word pairs ("accepting bogus") win on rarity.
        # Real phrases are boosted because they are more informative than single words.
        scored = {t: c * self.idf(t) * (1.5 if " " in t else 1.0) for t, c in counts.items()
                  if " " not in t or c > 1 or self.doc_freq[t] > 1}
        keywords: list[str] = []
        for term in sorted(scored, key=lambda t: (-scored[t], t)):
            # Skip a unigram already covered by a chosen bigram (and vice versa).
            if any(term in kw.split() or kw in term.split() for kw in keywords):
                continue
            keywords.append(term)
            if len(keywords) == k:
                break
        return keywords
