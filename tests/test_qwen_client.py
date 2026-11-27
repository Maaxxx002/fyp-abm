"""
Offline tests of src/qwen_client.py's request ledger (C59) and settings (A79). No network.
"""
import json
import threading

import pytest

import qwen_client as qc


def test_settings_are_a79():
    assert qc.SAMPLING == dict(temperature=0.7, top_p=0.8, presence_penalty=1.5)
    assert qc.EXTRA_BODY == {"enable_thinking": False, "top_k": 20}
    assert qc.SETTINGS["model"] == "qwen3.8-flash" and qc.SETTINGS["max_tokens"] == 1024


def test_ledger_cap_is_exact_under_concurrent_reservations(tmp_path):
    path = str(tmp_path / "requests.jsonl")
    led, got, capped = qc.Ledger(path), [], []

    def worker():
        for _ in range(25):
            try:
                got.append(led.reserve(50, dict(key="k")))
            except qc.RequestCapReached:
                capped.append(1)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    lines = [json.loads(x) for x in open(path, encoding="utf-8")]
    assert sorted(got) == list(range(1, 51)) and len(capped) == 150
    assert sorted(x["i"] for x in lines) == list(range(1, 51))


def test_ledger_count_survives_restart_and_counts_a_torn_line(tmp_path):
    path = str(tmp_path / "requests.jsonl")
    led = qc.Ledger(path)
    for _ in range(3):
        led.reserve(5, dict(key="k"))
    with open(path, "a", encoding="utf-8") as f:
        f.write('{"i": 4, "key": "k"')            # a line torn by a crash mid-write
    led2 = qc.Ledger(path)
    assert led2.n == 4
    led2.reserve(5, dict(key="k"))
    with pytest.raises(qc.RequestCapReached):
        led2.reserve(5, dict(key="k"))
    assert open(path, encoding="utf-8").read().count("\n") == 5
