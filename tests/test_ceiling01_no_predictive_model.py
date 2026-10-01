"""## Executive summary (read this first)

Verify a frozen CEILING-01 diagnostic contract.
"""

from pathlib import Path
import ast

def test_no_predictive_model_or_cli_hook():
 root=Path(__file__).resolve().parents[1]; package=root/'qfbench2_track_forecasting/ceiling01'
 assert 'ceiling01' not in (root/'qfbench2_track_forecasting/cli.py').read_text()
 assert 'ceiling01' not in (root/'Dockerfile').read_text()
 for path in package.glob('*.py'):
  tree=ast.parse(path.read_text())
  assert not any(isinstance(n,ast.Import) and any(a.name.startswith(('torch','sklearn','tensorflow')) for a in n.names) for n in ast.walk(tree))
