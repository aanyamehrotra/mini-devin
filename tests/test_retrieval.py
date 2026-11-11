import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.memory.vector_store import LocalIndex


class RetrievalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def test_relevant_code_ranks_above_unrelated_docs(self):
        self.write('runner.py', 'def validate_in_docker():\n    return "sandbox execution"')
        self.write('ui.md', 'React renders file tabs and browser buttons.')
        hits = LocalIndex.from_directory(self.root).search('validate Docker sandbox')
        self.assertEqual(hits[0]['source'], 'runner.py')
        self.assertEqual(hits[0]['citation'], 'runner.py:1-2')
        self.assertGreater(hits[0]['score'], 0)

    def test_line_provenance_and_overlap(self):
        self.write('docs.md', '\n'.join(f'line{i}' for i in range(1, 9)))
        chunks = LocalIndex.from_directory(self.root, chunk_lines=4, overlap=1).chunks
        self.assertEqual([(c.start_line,c.end_line) for c in chunks], [(1,4),(4,7),(7,8)])
        self.assertEqual(chunks[1].text, 'line4\nline5\nline6\nline7')

    def test_hidden_generated_and_symlink_files_excluded(self):
        self.write('.env', 'secret')
        self.write('.private/hidden.py', 'secret')
        self.write('node_modules/pkg/main.js', 'secret')
        self.write('workspace/generated.py', 'secret')
        self.write('safe.md', 'allowed context')
        with tempfile.TemporaryDirectory() as outside:
            source=Path(outside)/'outside.py';source.write_text('secret')
            (self.root/'escape.py').symlink_to(source)
            hits=LocalIndex.from_directory(self.root).search('secret')
        self.assertEqual(hits, [])

    def test_empty_and_no_match_queries(self):
        self.write('file.md','hello world')
        index=LocalIndex.from_directory(self.root)
        self.assertEqual(index.search(''), [])
        self.assertEqual(index.search('unrelatedword'), [])

    def test_ties_are_deterministic_and_top_k_bounded(self):
        self.write('a.md','identical')
        self.write('b.md','identical')
        index=LocalIndex.from_directory(self.root)
        self.assertEqual(index.search('identical', 1)[0]['source'], 'a.md')
        for value in [0,11,True]:
            with self.assertRaises(ValueError):index.search('word',value)

    def test_non_utf8_null_bytes_and_large_files_skipped(self):
        (self.root/'binary.txt').write_bytes(b'\xff\xfe')
        self.write('null.py','hello\x00world')
        self.write('big.md','x'*100)
        with patch('app.memory.vector_store.MAX_FILE_BYTES',50):
            index=LocalIndex.from_directory(self.root)
        self.assertEqual(index.chunks, [])
        self.assertEqual(index.stats['skipped_files'],3)

    def test_file_and_chunk_budgets(self):
        self.write('a.md','one\ntwo\nthree')
        self.write('b.md','four')
        with patch('app.memory.vector_store.MAX_FILES',1):
            index=LocalIndex.from_directory(self.root)
        self.assertEqual(index.stats['indexed_files'],1)
        self.assertTrue(index.stats['limit_reached'])
        with patch('app.memory.vector_store.MAX_CHUNKS',1):
            index=LocalIndex.from_directory(self.root,chunk_lines=1,overlap=0)
        self.assertEqual(len(index.chunks),1)
        self.assertTrue(index.stats['limit_reached'])

    def test_total_byte_budget(self):
        self.write('a.md','alpha')
        with patch('app.memory.vector_store.MAX_TOTAL_BYTES',2):
            index=LocalIndex.from_directory(self.root)
        self.assertEqual(index.chunks,[])
        self.assertTrue(index.stats['limit_reached'])

    def test_long_chunk_marks_truncation(self):
        self.write('a.md','abcdefghij')
        with patch('app.memory.vector_store.MAX_CHUNK_CHARS',5):
            chunk=LocalIndex.from_directory(self.root).chunks[0]
        self.assertEqual(chunk.text,'abcde')
        self.assertTrue(chunk.truncated)

    def test_invalid_chunk_configuration(self):
        with self.assertRaises(ValueError):LocalIndex.from_directory(self.root,chunk_lines=10,overlap=10)


class ContextApiTests(unittest.TestCase):
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)

    def test_disabled_without_configured_root(self):
        with patch.dict('os.environ',{'RAG_ROOT':''}), self.client() as client:
            self.assertEqual(client.post('/context/search',json={'query':'Docker'}).status_code,503)

    def test_search_returns_relative_sources_and_rebuilds_after_change(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict('os.environ',{'RAG_ROOT':folder}), self.client() as client:
            path=Path(folder)/'docs.md';path.write_text('docker sandbox')
            first=client.post('/context/search',json={'query':'docker'}).json()
            self.assertEqual(first['matches'][0]['source'],'docs.md')
            path.write_text('unrelated topic')
            self.assertEqual(client.post('/context/search',json={'query':'docker'}).json()['matches'],[])

    def test_invalid_top_k_and_unavailable_root(self):
        with self.client() as client:
            self.assertEqual(client.post('/context/search',json={'query':'test','top_k':11}).status_code,422)
            with patch.dict('os.environ',{'RAG_ROOT':'/does-not-exist'}):
                response=client.post('/context/search',json={'query':'test'})
            self.assertEqual(response.status_code,503)
            self.assertNotIn('/does-not-exist',response.text)
