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
- **Synchronized Code Editor:** Displays source code with real-time line highlighting indicating the currently executing statement.
- **Interactive Execution Controls:**
  - **Step Forward / Step Back:** Step through recorded execution event by event.
  - **Auto Play / Pause:** Continuous playback with adjustable speed slider.
  - **Reset:** Return instantly to the initial array state.
- **Input Presets:** Quick buttons to test Random, Reverse-sorted, Sorted, Duplicate, and Negative arrays.

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
    └── graph_canvas.py         # Circular graph rendering and traversal highlights
```

---

## Verified Algorithms

Trace has been validated against all five initial sorting algorithms:
1. **Bubble Sort** (in-place)
2. **Selection Sort** (in-place)
3. **Insertion Sort** (in-place)
4. **Quick Sort** (in-place partition)
5. **Merge Sort** (in-place sub-array merging)

Graph traversal tracking is validated with BFS over adjacency lists and matrices, including frontier/explored state and active-edge highlighting.
