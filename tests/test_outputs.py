import json
import os
import subprocess
from pathlib import Path


WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))
TESTS = Path(os.environ.get("TESTS_DIR", "/tests"))
SOLVER_PATH = WORKSPACE / "solution" / "solve.py"


def expected_state(instance):
    n = instance["n"]
    bits = [int(ch) for ch in instance["initial"]]
    tokens = [token.copy() for token in instance["tokens"]]

    for tick in range(instance["ticks"]):
        proposals = []
        for token in tokens:
            move = token["moves"][tick % len(token["moves"])]
            dest = token["pos"]
            if move == "L":
                dest = (dest - 1) % n
            elif move == "R":
                dest = (dest + 1) % n
            elif move != "S":
                raise AssertionError("invalid move in test data")
            proposals.append(dest)

        counts = {dest: proposals.count(dest) for dest in set(proposals)}
        for token, dest in zip(tokens, proposals):
            if counts[dest] >= 2:
                bits[token["pos"]] ^= 1
            else:
                token["pos"] = dest
                bits[dest] ^= 1

    return "".join(str(bit) for bit in bits)


def load_instances(path):
    with path.open() as f:
        return json.load(f)["instances"]


def run_solver(path):
    completed = subprocess.run(
        ["python3", str(SOLVER_PATH), str(path)],
        cwd=WORKSPACE,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )
    assert completed.returncode == 0, "solver exited unsuccessfully"
    return json.loads(completed.stdout)


def check_file(path):
    submitted = run_solver(path)
    assert isinstance(submitted, dict), "answer file must contain a JSON object"
    answers = submitted.get("answers")
    assert isinstance(answers, dict), "answer file must contain an answers object"

    expected = {case["id"]: expected_state(case) for case in load_instances(path)}
    assert set(answers) == set(expected), "answer ids do not match required ids"

    wrong = [case_id for case_id, value in expected.items() if answers.get(case_id) != value]
    assert not wrong, "one or more answers are incorrect: " + ", ".join(sorted(wrong))


def test_solver_file_exists():
    assert SOLVER_PATH.exists(), "missing solution/solve.py"


def test_public_answers_are_exact():
    check_file(TESTS / "public_instances.json")


def test_hidden_answers_are_exact():
    check_file(TESTS / "hidden_instances.json")


if __name__ == "__main__":
    test_solver_file_exists()
    test_public_answers_are_exact()
    test_hidden_answers_are_exact()
