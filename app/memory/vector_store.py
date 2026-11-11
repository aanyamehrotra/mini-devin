"""Bounded local lexical retrieval with file/line provenance (no embeddings)."""

from collections import Counter
from dataclasses import dataclass, asdict
import math
import os
from pathlib import Path
import re

EXTENSIONS = {'.py', '.md', '.rst', '.txt', '.js', '.jsx', '.ts', '.tsx'}
EXCLUDED = {'node_modules', 'workspace', 'venv', 'dist', 'build', 'outputs', '__pycache__'}
MAX_FILE_BYTES = 256 * 1024
MAX_TOTAL_BYTES = 4 * 1024 * 1024
MAX_FILES = 200
MAX_CHUNKS = 2000
MAX_CHUNK_CHARS = 12000


def tokens(text):
    identifiers = re.findall(r'[A-Za-z][A-Za-z0-9_]*', text)
    words = []
    for identifier in identifiers:
        words.append(identifier.lower())
        split = re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', identifier).replace('_', ' ')
        if split.lower() != identifier.lower():
            words.extend(split.lower().split())
    return Counter(words)


@dataclass(frozen=True)
class Chunk:
    source: str
    start_line: int
    end_line: int
    text: str
    truncated: bool = False


class LocalIndex:
    def __init__(self, chunks, *, indexed_files=0, skipped_files=0, limit_reached=False):
        self.chunks = list(chunks)
        self.stats = {'indexed_files': indexed_files, 'chunks': len(self.chunks),
                      'skipped_files': skipped_files, 'limit_reached': limit_reached}
        self.counts = [tokens(c.source + '\n' + c.text) for c in self.chunks]
        frequency = Counter(term for counts in self.counts for term in counts)
        self.idf = {term: math.log(1 + len(self.chunks) / (1 + count)) for term, count in frequency.items()}
        self.vectors = [self._vector(counts) for counts in self.counts]

    def _vector(self, counts):
        weights = {term: (1 + math.log(count)) * self.idf[term]
                   for term, count in counts.items() if term in self.idf}
        norm = math.sqrt(sum(value * value for value in weights.values()))
        return {term: value / norm for term, value in weights.items()} if norm else {}

    @classmethod
    def from_directory(cls, directory, *, chunk_lines=60, overlap=10):
        if type(chunk_lines) is not int or type(overlap) is not int or not 0 <= overlap < chunk_lines:
            raise ValueError('Require 0 <= overlap < chunk_lines')
        root = Path(directory).resolve(strict=True)
        if not root.is_dir():
            raise ValueError('Corpus root must be a directory')
        chunks = []
        indexed = skipped = total = 0
        limited = False
        for folder, dirs, names in os.walk(root, followlinks=False):
            dirs[:] = sorted(d for d in dirs if not d.startswith('.') and d not in EXCLUDED
                             and not (Path(folder) / d).is_symlink())
            for name in sorted(names):
                path = Path(folder) / name
                if name.startswith('.') or path.suffix.lower() not in EXTENSIONS or path.is_symlink():
                    skipped += 1
                    continue
                if indexed >= MAX_FILES or len(chunks) >= MAX_CHUNKS:
                    limited = True
                    break
                try:
                    if not path.resolve().is_relative_to(root):
                        skipped += 1
                        continue
                    with path.open('rb') as stream:
                        raw = stream.read(MAX_FILE_BYTES + 1)
                    if len(raw) > MAX_FILE_BYTES:
                        skipped += 1
                        continue
                    if total + len(raw) > MAX_TOTAL_BYTES:
                        limited = True
                        skipped += 1
                        continue
                    text = raw.decode('utf-8')
                    if '\x00' in text:
                        skipped += 1
                        continue
                except (OSError, UnicodeError):
                    skipped += 1
                    continue
                total += len(raw)
                indexed += 1
                lines = text.splitlines()
                for start in range(0, len(lines), chunk_lines - overlap):
                    if len(chunks) >= MAX_CHUNKS:
                        limited = True
                        break
                    end = min(start + chunk_lines, len(lines))
                    content = '\n'.join(lines[start:end])
                    if content.strip():
                        chunks.append(Chunk(path.relative_to(root).as_posix(), start + 1, end,
                                            content[:MAX_CHUNK_CHARS], len(content) > MAX_CHUNK_CHARS))
                    if end == len(lines):
                        break
            if indexed >= MAX_FILES or len(chunks) >= MAX_CHUNKS:
                limited = True
                break
        return cls(chunks, indexed_files=indexed, skipped_files=skipped, limit_reached=limited)

    def search(self, query, top_k=5):
        if type(top_k) is not int or not 1 <= top_k <= 10:
            raise ValueError('top_k must be between 1 and 10')
        vector = self._vector(tokens(query))
        ranked = []
        for chunk, document in zip(self.chunks, self.vectors):
            score = sum(value * document.get(term, 0) for term, value in vector.items())
            if score > 0:
                ranked.append((score, chunk))
        ranked.sort(key=lambda pair: (-pair[0], pair[1].source, pair[1].start_line))
        return [{**asdict(chunk), 'score': round(score, 6),
                 'citation': f'{chunk.source}:{chunk.start_line}-{chunk.end_line}'}
                for score, chunk in ranked[:top_k]]
