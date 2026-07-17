import json
import os
import subprocess
from itertools import combinations
from pathlib import Path


WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/workspace"))
TESTS = Path(os.environ.get("TESTS_DIR", "/tests"))
SOLVER_PATH = WORKSPACE / "solution" / "solve.py"


def occurrence_count(scroll, pattern):
    alternatives = pattern if isinstance(pattern, list) else [pattern]
    return sum(
        1
        for start in range(len(scroll))
        if any(scroll.startswith(alternative, start) for alternative in alternatives)
    )


def chant_mask(instance, chant):
    lock_index = {lock["name"]: i for i, lock in enumerate(instance["locks"])}
    mask = 0
    for motif in chant["motifs"]:
        if occurrence_count(chant["scroll"], motif["pattern"]) % 2 == 1:
            mask ^= 1 << lock_index[motif["lock"]]
    return mask


def state_mask(bits):
    mask = 0
    for i, bit in enumerate(bits):
        if bit == "1":
            mask |= 1 << i
    return mask


def apply_subset(instance, chosen):
    mask = state_mask(instance["initial"])
    chants = {chant["name"]: chant for chant in instance["chants"]}
    for name in sorted(chosen):
        mask ^= chant_mask(instance, chants[name])
    return "".join("1" if mask >> i & 1 else "0" for i in range(len(instance["locks"])))


def expected_answer(instance):
    names = sorted(chant["name"] for chant in instance["chants"])
    matches = []
    for size in range(len(names) + 1):
        for subset in combinations(names, size):
            if apply_subset(instance, subset) == instance["target"]:
                matches.append("+".join(subset) if subset else "NONE")
    assert matches, f"{instance['id']} has no valid answer"
    return min(matches)


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
    assert completed.returncode == 0, (
        "solver exited unsuccessfully\n"
        f"stdout:\n{completed.stdout}\n"
        f"stderr:\n{completed.stderr}"
    )
    return json.loads(completed.stdout)


def check_file(path):
    submitted = run_solver(path)
    assert isinstance(submitted, dict), "answer file must contain a JSON object"
    answers = submitted.get("answers")
    assert isinstance(answers, dict), "answer file must contain an answers object"

    expected = {case["id"]: expected_answer(case) for case in load_instances(path)}
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
