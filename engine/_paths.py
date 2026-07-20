"""_paths.py — put the repo root on sys.path so `import config` resolves when an
engine script is run directly (python engine/foo.py).

The bootstrap block used to be copy-pasted into every engine script. Import this
first instead:

    import _paths   # noqa: F401  (side-effect: adds repo root to sys.path)
    import config

Idempotent and dependency-free. `_paths.ROOT` is the repo root, for the few
scripts that also need it as a value.
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
