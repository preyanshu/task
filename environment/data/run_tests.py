import json
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_solver(level):
    with tempfile.TemporaryDirectory() as d:
        inp = Path(d) / 'level.json'
        out = Path(d) / 'out.json'
        inp.write_text(json.dumps({k: v for k, v in level.items() if k not in {'id', 'expected_commands'}}))
        proc = subprocess.run(['python3', str(ROOT / 'solve.py'), str(inp), str(out)], capture_output=True, text=True, timeout=10)
        assert proc.returncode == 0, proc.stderr
        return json.loads(out.read_text())['commands']


def main():
    levels = json.loads((ROOT / 'levels_public.json').read_text())['levels']
    for level in levels:
        actual = run_solver(level)
        expected = level['expected_commands']
        if actual != expected:
            raise AssertionError(f"{level['id']}: expected {expected}, got {actual}")
        print(f"{level['id']}: ok")


if __name__ == '__main__':
    main()
