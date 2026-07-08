import json


def read_records(path):
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows


def total(rows, field):
    s = 0
    for r in rows:
        s += r[field]
    return s
