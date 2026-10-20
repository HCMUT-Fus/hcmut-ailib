"""Generate BibTeX, APA 7 and IEEE citations for arXiv papers."""

from __future__ import annotations

import re

from src.search_engine import Paper


def split_name(full_name: str) -> tuple[str, list[str]]:
    """'Nguyen Van An' -> ('An', ['Nguyen', 'Van']): last token is the family name."""
    parts = full_name.split()
    if len(parts) <= 1:
        return full_name, []
    return parts[-1], parts[:-1]


def initials(given: list[str]) -> str:
    """['Jean-Pierre', 'K.'] -> 'J.-P. K.'"""
    return " ".join("-".join(f"{piece[0]}." for piece in name.split("-") if piece)
                    for name in given)


def arxiv_doi(paper: Paper) -> str:
    """Publisher DOI when known, otherwise the DataCite DOI every arXiv paper has."""
    return paper.doi or f"10.48550/arXiv.{paper.id}"


def bibtex_key(paper: Paper) -> str:
    family = split_name(paper.authors[0])[0] if paper.authors else "anon"
    word = next((w for w in re.findall(r"[A-Za-z]+", paper.title) if len(w) > 3), "paper")
    return re.sub(r"[^a-z0-9]", "", f"{family}{paper.year}{word}".lower())


def to_bibtex(paper: Paper) -> str:
    fields = {
        "title": "{" + paper.title.replace("&", r"\&") + "}",
        "author": " and ".join(paper.authors),
        "year": str(paper.year),
        "eprint": paper.id,
        "archivePrefix": "arXiv",
        "primaryClass": paper.primary_category,
        "doi": arxiv_doi(paper),
        "url": paper.abs_url,
    }
    body = ",\n".join(f"  {name} = {{{value}}}" for name, value in fields.items())
    return f"@misc{{{bibtex_key(paper)},\n{body}\n}}"


def to_apa(paper: Paper) -> str:
    names = [f"{family}, {initials(given)}".rstrip(", ")
             for family, given in map(split_name, paper.authors)]
    if len(names) > 20:  # APA 7: first 19, ellipsis, final author
        author_text = ", ".join(names[:19]) + ", . . . " + names[-1]
    elif len(names) > 1:
        author_text = ", ".join(names[:-1]) + ", & " + names[-1]
    else:
        author_text = names[0] if names else "Anonymous"
    return (f"{author_text} ({paper.year}). {paper.title} (arXiv:{paper.id}). arXiv. "
            f"https://doi.org/{arxiv_doi(paper)}")


def to_ieee(paper: Paper) -> str:
    names = [f"{initials(given)} {family}".strip()
             for family, given in map(split_name, paper.authors)]
    if len(names) > 6:  # IEEE: more than six authors -> first author et al.
        author_text = f"{names[0]} et al."
    elif len(names) > 1:
        author_text = ", ".join(names[:-1]) + (", and " if len(names) > 2 else " and ") + names[-1]
    else:
        author_text = names[0] if names else "Anonymous"
    return f'{author_text}, "{paper.title}," arXiv preprint arXiv:{paper.id}, {paper.year}.'


FORMATS = {"BibTeX": to_bibtex, "APA": to_apa, "IEEE": to_ieee}
