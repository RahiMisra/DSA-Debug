# Trace — Algorithm Execution Visualizer

Trace is a Python desktop application designed to help users understand and debug algorithms by visualizing their actual execution.

Rather than relying on predefined animations, Trace executes user-submitted Python sorting code in an isolated environment, records every line execution, array access, comparison, swap, and mutation, and visualizes the algorithm step-by-step.

---

## Features

- **Actual Code Execution:** Runs the user's submitted Python code rather than playing a canned animation.
- **Subprocess Isolation:** User code executes in a separate process with configurable timeout enforcement to protect against runaway programs or infinite loops.
- **AST Tracing & Instrumentation:** Accurately detects and records comparisons (`<`, `>`, `<=`, etc.), element swaps (`arr[i], arr[j] = arr[j], arr[i]`), element writes (`arr[i] = ...`), and reads.
- **Visual Array Canvas:** Box-style cells with centered values and index labels (with an optional bar view).
- **Operation Highlighting:**
  - 🟡 **Amber / Yellow:** Comparing elements
  - 🔴 **Red:** Swapping elements
  - 🟣 **Purple:** Modifying / writing elements
  - 🟢 **Emerald:** Reading elements
- **Linked List & Binary Tree Views:** Pointer labels, node mutations, cycle arrows, and hierarchical tree layout.
- **Graph View:** Circular vertex layout with directed/undirected edges, self-loops, and frontier/explored/current-node highlighting during BFS and DFS.
- **Stack & Queue Panels:** Detects auxiliary stacks and queues (`stack`, `st`, `s`, `queue`, `q`, `fifo`, deques) and renders vertical LIFO towers and horizontal FIFO pipes with push/pop/enqueue/dequeue transitions.
- **Hash Map & Set Panels:** Detects frequency maps, lookup tables, memo tables, and visited sets (`freq`, `count`, `memo`, `dp`, `table`, `visited`, `seen`, …) and renders key/value rows and membership badges with active-key/active-member highlighting.
- **Recursion & Subwork Panel:** Tracks recursive call frames with depth, arguments, and return values; renders the active call stack deepest-first, intermediate list slices and recursive sub-array arguments, and a dedicated returned-structure panel.
- **LeetCode `class Solution:` Support:** Auto-detects `Solution` classes, instantiates them, and runs bound methods with `self` handled automatically. Supports multi-parameter inputs such as `head`, `l1`/`l2`, `root`/`p`/`q`, grids, and `adjList` object graphs.
- **Segmented Multi-View Dashboard:** Primary structure stays in the main viewport while stack/queue, hash map/set, recursion, sub-array, and returned-structure segments appear below when relevant. A draggable splitter separates the primary viewport from the workspace, the workspace splits auxiliary and subwork side by side, and every panel has a header with a collapse/expand control. Panel visibility and collapse state persist while stepping.
- **Scrollable, Zoom-Free Viewports:** Wide arrays, long linked lists, large trees/graphs, deep call stacks, and long stack/queue/hash content render at a readable natural size. Scrollbars appear only when needed, and the view supports mouse-wheel vertical scrolling, Shift+wheel horizontal scrolling, and click-drag background panning.
- **Click-to-Expand Truncated Text:** Long node labels, pointer lists, hash keys/values, set members, recursion frame labels, sub-array items, and returned structures show an ellipsis. Clicking one opens a read-only detail window with the full wrapped/scrollable value; close it with ✕, Escape, or by clicking elsewhere.
- **Synchronized Code Editor:** Displays source code with real-time line highlighting indicating the currently executing statement.
- **Interactive Execution Controls:**
  - **Step Forward / Step Back:** Step through recorded execution event by event.
  - **Auto Play / Pause:** Continuous playback with adjustable speed slider.
  - **Reset:** Return instantly to the initial array state.
- **Runnable Preset Library:** One-click LeetCode examples for Array, String, Linked List, Binary Tree, Graph, Stack/Queue, and Hash Map/Set, each loading a matching input and default algorithm. The Array preset generates a fresh random array on every click.

---

## UI Style

All colours and control styling come from `src/visualization/theme.py`. The palette uses a darkened three-level base (`#0B0B12`, `#12121A`, `#1A1A24`) with preserved Catppuccin accents, WCAG AA text contrast, and ttk `clam` scrollbars with themed trough, thumb, hover, and pressed states. Panels use a 1 px inset border and visible header/dashboard dividers; array cells and tree, graph, and linked-list nodes use cheap static inset lines or 2 px offset shadows for depth. Change the palette in `theme.py` rather than editing individual widgets.

---

## Prerequisites

- Python 3.10+ (tested on Python 3.12)
- Tkinter (included with standard Python on Windows and macOS)

---

## Setup

Install testing dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Application

Launch the desktop interface:

```bash
python -m src.main
```

or:

```bash
python src/main.py
```

---

## Running Tests

Execute the automated test suite with pytest:

```bash
python -m pytest
```

---

## Project Structure

```text
src/
├── main.py                     # Application entry point
├── ui/
│   ├── main_window.py          # Main desktop window integrating all components
│   ├── code_editor.py          # Code editor with line numbering and highlighting
│   ├── input_panel.py          # Array input, presets, and function name selector
│   ├── presets.py              # Single source of preset inputs and default algorithms
│   ├── array_view.py           # Tkinter canvas rendering dynamic array bars
│   └── execution_controls.py   # Step forward/back, play/pause, reset, speed slider
├── execution/
│   ├── runner.py               # Subprocess execution manager with timeouts
│   ├── worker.py               # Worker script running user code with stdout isolation
│   ├── tracer.py               # Tracing engine combining sys.settrace & runtime hooks
│   ├── events.py               # ExecutionEvent and ExecutionHistory models
│   ├── instrumentation.py      # AST NodeTransformer rewriting comparisons & mutations
│   ├── models.py               # ListNode, TreeNode, and normalized Graph models
│   ├── parsers.py              # LeetCode-style input parsing
│   └── result.py               # ExecutionResult and ExecutionError models
└── visualization/
    ├── array_state.py          # ArrayViewState and ElementHighlight definitions
    ├── event_processor.py      # Translates ExecutionEvents into visual states
    ├── linked_list_canvas.py   # Node/arrow linked list rendering
    ├── tree_canvas.py          # Hierarchical binary tree rendering
    ├── graph_canvas.py         # Circular graph rendering and traversal highlights
    ├── auxiliary_canvas.py     # Stack towers and queue pipes with operation transitions
    ├── hash_canvas.py          # Map key/value tables and set membership badges
    ├── recursion_canvas.py     # Call stack, sub-array rows, and returned structure
    ├── panel.py                # Collapsible panel with a persistent header
    ├── viewport.py             # Scrollable canvas wrapper (scrollbars, wheel, drag pan)
    ├── text_detail.py          # Truncation helpers and click-to-expand detail popup
    ├── theme.py                # Central palette, semantic colour maps, and ttk styling
    └── dashboard.py            # Resizable primary + auxiliary + subwork segmented layout
```

---

## Verified Algorithms

Trace has been validated against all five initial sorting algorithms:
1. **Bubble Sort** (in-place)
2. **Selection Sort** (in-place)
3. **Insertion Sort** (in-place)
4. **Quick Sort** (in-place partition)
5. **Merge Sort** (in-place sub-array merging)

Graph traversal tracking is validated with BFS over adjacency lists and matrices, including frontier/explored state and active-edge highlighting. Stack and queue tracking is validated with LIFO/FIFO sequences, container snapshots, and operation highlighting. Hash map and set tracking is validated with dict insert/update/lookup/membership operations, set add/remove/membership operations, active-key highlighting, and simultaneous queue + visited-set panels. Recursion tracking is validated with recursive factorial call frames/returns, merge-sort slice and recursive-argument sub-arrays, returned structures, and call-stack panel synchronization.

LeetCode Solution integration is validated end-to-end for Reverse Linked List, Merge Two Sorted Lists, Maximum Depth, Invert Binary Tree, Validate BST, Number of Islands, Clone Graph, Valid Parentheses, a queue built from stacks, Two Sum, and Group Anagrams. The dashboard suite also verifies that primary, auxiliary, sub-array, and returned-structure segments can be displayed together.
