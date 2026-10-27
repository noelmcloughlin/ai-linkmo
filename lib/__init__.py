"""ai-linkmo's own code, beside the linkmo project in ai-risk-ontology-linkmo/.

That project's package, ai_linkmo, is not installed in this project's environment, so its
src/ goes on the path when lib is imported.
"""

import sys
from pathlib import Path

_LINKMO_SRC = Path(__file__).resolve().parent.parent / "ai-risk-ontology-linkmo" / "src"
if str(_LINKMO_SRC) not in sys.path:
    sys.path.append(str(_LINKMO_SRC))
