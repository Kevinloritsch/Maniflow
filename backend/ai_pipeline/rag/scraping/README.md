**EACH SCRAPING FILE HAS THEIR OWN DOCUMENTATION (except compile.py, which is this \/)

Three commands:

  python compile.py scrape    — scrape all sources → clean → export .txt review file
  python compile.py ingest    — parse approved chunks from .txt → build VectorStore
  python compile.py stats     — print review queue statistics

Review file: education_training_data.txt
Each chunk is delimited like this:

  ════════════════════════════════════════════════════════════════
  CHUNK 0042 | trees > binary_search_tree > insertion | openstax
  APPROVED: null        ← change to YES or NO
  URL: https://openstax.org/books/introduction-computer-science/pages/3-1-introduction-to-data-strutures-and-algorithms
  TITLE: OpenStax (introduction-computer-science): binary_search_tree — insertion
  CHARS: 842  CODE BLOCKS: 2
  ────────────────────────────────────────────────────────────────
  BST insertion works by comparing the new value against the current
  node and recursively descending left or right...

  [CODE]
  def insert(node, value):
      if node is None:
          return Node(value)
      if value < node.val:
          node.left = insert(node.left, value)
      ...
  [/CODE]
  ════════════════════════════════════════════════════════════════

Editing instructions:
- Change "APPROVED: null" to "APPROVED: YES" to include the chunk
- Change "APPROVED: null" to "APPROVED: NO" to reject it
- Do NOT edit the CHUNK / URL / TITLE lines — the parser uses them
- You may edit or annotate the body text freely; it is not re-parsed
- Save as UTF-8

Workflow:
1. python compile.py scrape
2. Open ../education_training_data.txt and set APPROVED: YES / NO
3. python compile.py ingest
4. Vector store at ../vector_store/ is ready for rag.py