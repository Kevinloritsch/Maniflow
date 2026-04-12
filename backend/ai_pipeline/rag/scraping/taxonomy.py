"""
Structure for DSA topic tree:

Topic
  .name        : canonical name used as chunk metadata and folder key
  .subchapters : ordered list of subchapter names
  .keywords    : search terms used by scrapers to find the right page
  .wiki_title  : Wikipedia article title (None = skip Wikipedia)
  .so_tags     : StackOverflow tags to query
 
Each subchapter becomes its own chunk in the vector store, tagged with:
  {"category": "trees", "topic": "binary_search_tree", "subchapter": "insertion"} 
"""

from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class Topic: 
    name:               str
    subchapters:        list[str]
    keywords:           list[str]
    openstax_pages:     list[tuple[str, str]] = field(default_factory=list)
    wiki_title:         str | None  = None
    so_tags:           list[str]   = field(default_factory=list)
    
TAXONOMY: dict[str, list[Topic]] = {
 
    "arrays": [
        Topic(
            name        = "arrays_basics",
            subchapters = ["introduction", "indexing", "insertion", "deletion",
                           "searching", "sorting", "two_pointer", "sliding_window"],
            keywords    = ["array data structure", "array operations"],
            openstax_pages = [
                ("introduction-computer-science", "3-1-introduction-to-data-structures-and-algorithms"),
                ("introduction-computer-science", "3-2-algorithm-design-and-discovery"),
                ("introduction-computer-science", "3-5-sample-algorithms-by-problem"),
            ],
            wiki_title  = "Array (data structure)",
            so_tags     = ["arrays", "array-algorithms"],
        ),
    ],
 
    "linked_lists": [
        Topic(
            name        = "singly_linked_list",
            subchapters = ["introduction", "insertion", "deletion", "traversal",
                           "search", "reversal"],
            keywords    = ["singly linked list", "linked list operations"],
            openstax_pages = [
                ("introduction-computer-science", "3-1-introduction-to-data-structures-and-algorithms"),
            ],
            wiki_title  = "Linked list",
            so_tags     = ["linked-list"],
        ),
        Topic(
            name        = "doubly_linked_list",
            subchapters = ["introduction", "insertion", "deletion", "traversal"],
            keywords    = ["doubly linked list"],
            openstax_pages = [],
            wiki_title  = "Doubly linked list",
            so_tags     = ["doubly-linked-list"],
        ),
        Topic(
            name        = "circular_linked_list",
            subchapters = ["introduction", "insertion", "deletion"],
            keywords    = ["circular linked list"],
            openstax_pages = [],   
            wiki_title  = "Linked list#Circular linked list",
            so_tags     = ["circular-linked-list"],
        ),
    ],
 
    "stacks_queues": [
        Topic(
            name        = "stack",
            subchapters = ["introduction", "push", "pop", "peek",
                           "applications", "implementation"],
            keywords    = ["stack data structure", "LIFO"],
            openstax_pages = [
                ("introduction-computer-science", "3-5-sample-algorithms-by-problem"),  #surprisingly not a lot of coverage
            ],
            wiki_title  = "Stack (abstract data type)",
            so_tags     = ["stack"],
        ),
        Topic(
            name        = "queue",
            subchapters = ["introduction", "enqueue", "dequeue",
                           "circular_queue", "deque", "priority_queue"],
            keywords    = ["queue data structure", "FIFO"],
            openstax_pages = [
                ("introduction-computer-science", "3-1-introduction-to-data-structures-and-algorithms"),
                ("introduction-computer-science", "3-2-algorithm-design-and-discovery"),
                ("introduction-computer-science", "3-5-sample-algorithms-by-problem"),
            ],
            wiki_title  = "Queue (abstract data type)",
            so_tags     = ["queue"],
        ),
    ],
 
    "trees": [
        Topic(
            name        = "binary_tree",
            subchapters = ["introduction", "insertion", "deletion", "search",
                           "inorder", "preorder", "postorder", "level_order",
                           "height", "diameter"],
            keywords    = ["binary tree", "tree traversal"],
            openstax_pages = [
                ("introduction-computer-science", "3-1-introduction-to-data-structures-and-algorithms"),
                ("introduction-computer-science", "3-2-algorithm-design-and-discovery"),
                ("introduction-computer-science", "3-5-sample-algorithms-by-problem"),
            ],
            wiki_title  = "Binary tree",
            so_tags     = ["binary-tree"],
        ),
        Topic(
            name        = "binary_search_tree",
            subchapters = ["introduction", "insertion", "deletion", "search",
                           "successor", "predecessor", "validation"],
            keywords    = ["binary search tree", "BST"],
            openstax_pages = [
                ("introduction-computer-science", "3-1-introduction-to-data-structures-and-algorithms"),
                ("introduction-computer-science", "3-2-algorithm-design-and-discovery"),
                ("introduction-computer-science", "3-5-sample-algorithms-by-problem"),
            ],
            wiki_title  = "Binary search tree",
            so_tags     = ["binary-search-tree"],
        ),
        Topic(
            name        = "avl_tree",
            subchapters = ["introduction", "rotations", "insertion",
                           "deletion", "balance_factor"],
            keywords    = ["AVL tree", "self-balancing BST"],
            openstax_pages = [
                ("introduction-computer-science", "3-1-introduction-to-data-structures-and-algorithms"),
                ("introduction-computer-science", "3-5-sample-algorithms-by-problem"),
            ],
            wiki_title  = "AVL tree",
            so_tags     = ["avl-tree"],
        ),
        Topic(
            name        = "red_black_tree",
            subchapters = ["introduction", "properties", "insertion",
                           "deletion", "rotation"],
            keywords    = ["red black tree"],
            openstax_pages = [],   # coverage sparse
            wiki_title  = "Red–black tree",
            so_tags     = ["red-black-tree"],
        ),
        Topic(
            name        = "trie",
            subchapters = ["introduction", "insertion", "search",
                           "deletion", "autocomplete"],
            keywords    = ["trie data structure", "prefix tree"],
            openstax_pages = [],
            wiki_title  = "Trie",
            so_tags     = ["trie"],
        ),
        Topic(
            name        = "segment_tree",
            subchapters = ["introduction", "build", "range_query",
                           "point_update", "lazy_propagation"],
            keywords    = ["segment tree", "range query"],
            openstax_pages = [],
            wiki_title  = "Segment tree",
            so_tags     = ["segment-tree"],
        ),
    ],
 
    "heaps": [
        Topic(
            name        = "heap",
            subchapters = ["introduction", "max_heap", "min_heap",
                           "heapify", "insertion", "deletion", "heap_sort"],
            keywords    = ["heap data structure", "binary heap"],
            openstax_pages = [
                ("introduction-computer-science", "3-1-introduction-to-data-structures-and-algorithms"),
                ("introduction-computer-science", "3-5-sample-algorithms-by-problem"),
            ],
            wiki_title  = "Heap (data structure)",
            so_tags     = ["heap", "priority-queue"],
        ),
    ],
 
    "hashing": [
        Topic(
            name        = "hash_table",
            subchapters = ["introduction", "hash_function", "collision_resolution",
                           "chaining", "open_addressing", "load_factor",
                           "insertion", "deletion", "search"],
            keywords    = ["hash table", "hash map", "hashing"],
            openstax_pages = [
                ("introduction-computer-science", "3-5-sample-alogrithms-by-problem"),
                ("introduction-computer-science", "3-6-computer-science-theory"),
            ],
            wiki_title  = "Hash table",
            so_tags     = ["hash-table", "hashmap"],
        ),
    ],
 
    "graphs": [
        Topic(
            name        = "graph_basics",
            subchapters = ["introduction", "adjacency_matrix",
                           "adjacency_list", "bfs", "dfs"],
            keywords    = ["graph data structure", "graph traversal"],
            openstax_pages = [
                ("introduction-computer-science", "3-1-introduction-to-data-structures-and-algorithms"),
                ("introduction-computer-science", "3-2-algorithm-design-and-discovery"),
            ],
            wiki_title  = "Graph (abstract data type)",
            so_tags     = ["graph", "graph-algorithm"],
        ),
        Topic(
            name        = "shortest_paths",
            subchapters = ["dijkstra", "bellman_ford", "floyd_warshall",
                           "a_star"],
            keywords    = ["shortest path algorithm", "Dijkstra"],
            openstax_pages = [
                ("introduction-computer-science", "3-5-sample-algorithms-by-problem"),
            ],
            wiki_title  = "Dijkstra's algorithm",
            so_tags     = ["dijkstra", "shortest-path"],
        ),
        Topic(
            name        = "minimum_spanning_tree",
            subchapters = ["introduction", "kruskal", "prim"],
            keywords    = ["minimum spanning tree", "Kruskal", "Prim"],
            openstax_pages = [
                ("introduction-computer-science", "3-4-algorithmic-paradigms"),
                ("introduction-computer-science", "3-5-sample-algorithms-by-problem"),
                ("introduction-computer-science", "3-6-computer-science-theory"),
            ],
            wiki_title  = "Minimum spanning tree",
            so_tags     = ["minimum-spanning-tree"],
        ),
        Topic(
            name        = "topological_sort",
            subchapters = ["introduction", "kahn_algorithm", "dfs_approach"],
            keywords    = ["topological sort", "topological ordering"],
            openstax_pages = [],
            wiki_title  = "Topological sorting",
            so_tags     = ["topological-sort"],
        ),
    ],
 
    "sorting": [
        Topic(
            name        = "comparison_sorts",
            subchapters = ["bubble_sort", "selection_sort", "insertion_sort",
                           "merge_sort", "quick_sort", "heap_sort"],
            keywords    = ["sorting algorithms", "comparison sort"],
            openstax_pages = [
                ("introduction-computer-science", "3-4-algorithmic-paradigms"),
                ("introduction-computer-science", "3-5-sample-algorithms-by-problem"),
                ("introduction-computer-science", "3-6-computer-science-theory"),    #probably not a lot of sorting info here
            ],
            wiki_title  = "Sorting algorithm",
            so_tags     = ["sorting", "sorting-algorithm"],
        ),
        Topic(
            name        = "linear_sorts",
            subchapters = ["counting_sort", "radix_sort", "bucket_sort"],
            keywords    = ["linear time sorting", "counting sort radix sort"],
            openstax_pages = [
                ("introduction-computer-science", "3-4-algorithmic-paradigms"),
                ("introduction-computer-science", "3-5-sample-algorithms-by-problem"),
                ("introduction-computer-science", "3-6-computer-science-theory"),    
            ],
            wiki_title  = "Counting sort",
            so_tags     = ["counting-sort", "radix-sort"],
        ),
    ],
 
    "dynamic_programming": [
        Topic(
            name        = "dp_fundamentals",
            subchapters = ["introduction", "memoization", "tabulation",
                           "overlapping_subproblems", "optimal_substructure"],
            keywords    = ["dynamic programming", "memoization tabulation"],
            openstax_pages = [
                ("introduction-computer-science", "3-4-algorithmic-paradigms"),
            ],
            wiki_title  = "Dynamic programming",
            so_tags     = ["dynamic-programming"],
        ),
        Topic(
            name        = "classic_dp",
            subchapters = ["fibonacci", "knapsack_01", "longest_common_subsequence",
                           "longest_increasing_subsequence", "coin_change",
                           "edit_distance", "matrix_chain"],
            keywords    = ["knapsack problem", "LCS dynamic programming"],
            openstax_pages = [
                ("introduction-computer-science", "10-2-classic-dp-problems"),
            ],
            wiki_title  = "Knapsack problem",
            so_tags     = ["knapsack-problem", "longest-common-subsequence"],
        ),
    ],
 
    "searching": [
        Topic(
            name        = "search_algorithms",
            subchapters = ["linear_search", "binary_search",
                           "jump_search", "interpolation_search",
                           "exponential_search"],
            keywords    = ["searching algorithms", "binary search"],
            openstax_pages = [
                ("introduction-computer-science", "3-2-algorithm-design-and-discovery"),
                ("introduction-computer-science", "3-3-formal-properties-of-algorithms"),
            ],
            wiki_title  = "Binary search algorithm",
            so_tags     = ["binary-search", "searching"],
        ),
    ],
 
    "greedy": [
        Topic(
            name        = "greedy_algorithms",
            subchapters = ["introduction", "activity_selection",
                           "huffman_coding", "fractional_knapsack",
                           "job_scheduling"],
            keywords    = ["greedy algorithm", "activity selection problem"],
            openstax_pages = [
                ("introduction-computer-science", "3-4-algorithmic-paradigms"),
            ],
            wiki_title  = "Greedy algorithm",
            so_tags     = ["greedy", "greedy-algorithm"],
        ),
    ],
 
    "backtracking": [
        Topic(
            name        = "backtracking",
            subchapters = ["introduction", "n_queens", "sudoku_solver",
                           "subset_sum", "permutations"],
            keywords    = ["backtracking algorithm", "N queens problem"],
            openstax_pages = [
                ("introduction-computer-science", "3-4-algorithmic-paradigms"),
                ("introduction-computer-science", "3-6-computer-science-theory"),    
            ],
            wiki_title  = "Backtracking",
            so_tags     = ["backtracking"],
        ),
    ],
}

def all_topics() -> list[tuple[str, Topic]]:
    return [
        (cat, topic)
        for cat, topics in TAXONOMY.items()
        for topic in topics
    ]

def topic_count() -> int:
    return sum(len(v) for v in TAXONOMY.values())
 
 
def subchapter_count() -> int:
    return sum(
        len(t.subchapters)
        for topics in TAXONOMY.values()
        for t in topics
    )
 
 
if __name__ == "__main__":
    print(f"Categories  : {len(TAXONOMY)}")
    print(f"Topics      : {topic_count()}")
    print(f"Subchapters : {subchapter_count()}")
