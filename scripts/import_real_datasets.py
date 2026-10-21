"""
Real-World Dataset Importer (NSL-KDD)
=====================================
Converts the locally downloaded NSL-KDD benchmark (KDDTrain+.txt /
KDDTest+.txt, from https://raw.githubusercontent.com/defcom17/NSL_KDD/master/)
into clean CSVs and registers them as PUBLIC DATASET rows.

NSL-KDD is a cleaned descendant of the classic KDD Cup 1999 training set with
duplicate records removed. It has 41 network-flow features plus the class
label (attack vs normal). The raw files add a trailing difficulty column.

The conversion is purely local and offline; it does NOT re-download anything.
If the raw files are missing the script prints a clear message and exits
gracefully.
"""

import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config  # noqa: E402

HERE = os.path.join(config.DATASET_DIR, "real")
RAIN_RAW = os.path.join(HERE, "KDDTrain+.txt")
TEST_RAW = os.path.join(HERE, "KDDTest+.txt")

# 41 features used by the NSL-KDD benchmark (KDD Cup 1999 feature set)
NSL_FEATURES = [
    "duration",
    "protocol_type",
    "service",
    "flag",
    "src_bytes",
    "dst_bytes",
    "land",
    "wrong_fragment",
    "urgent",
    "hot",
    "num_failed_logins",
    "logged_in",
    "num_compromised",
    "root_shell",
    "su_attempted",
    "num_root",
    "num_file_creations",
    "num_shells",
    "num_access_files",
    "num_outbound_cmds",
    "is_host_login",
    "is_guest_login",
    "count",
    "srv_count",
    "serror_rate",
    "srv_serror_rate",
    "rerror_rate",
    "srv_rerror_rate",
    "same_srv_rate",
    "diff_srv_rate",
    "srv_diff_host_rate",
    "dst_host_count",
    "dst_host_srv_count",
    "dst_host_same_srv_rate",
    "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate",
    "dst_host_srv_serror_rate",
    "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate",
]

CATEGORICAL = ["protocol_type", "service", "flag"]


def convert(raw_path, out_path, name):
    if not os.path.exists(raw_path):
        print(f"[skip] {name}: raw file missing ({raw_path})")
        return None
    df = pd.read_csv(
        raw_path, header=None, names=NSL_FEATURES + ["label", "difficulty"]
    )
    df["label"] = df["label"].astype(str).str.rstrip(".").str.lower()
    df["difficulty"] = pd.to_numeric(df["difficulty"], errors="coerce")
    df.to_csv(out_path, index=False)
    attacks = (df["label"] != "normal").sum()
    print(
        f"[ok]   {name}: {len(df):,} rows, {attacks:,} attack "
        f"({attacks / max(1, len(df)):.1%}) -> {os.path.basename(out_path)}"
    )
    return df


def main():
    os.makedirs(HERE, exist_ok=True)
    train = convert(RAIN_RAW, os.path.join(HERE, "nsl_kdd_train.csv"), "NSL-KDD train")
    test = convert(TEST_RAW, os.path.join(HERE, "nsl_kdd_test.csv"), "NSL-KDD test")
    if train is None and test is None:
        print(
            "No NSL-KDD raw files found. See README for the download URL, "
            "or re-run after placing KDDTrain+.txt / KDDTest+.txt in "
            f"{HERE}"
        )
        return 1

    # combined file for AI training (train + test)
    parts = [p for p in (train, test) if p is not None]
    if parts:
        combined = pd.concat(parts, ignore_index=True)
        out = os.path.join(HERE, "nsl_kdd_combined.csv")
        combined.to_csv(out, index=False)
        print(f"[ok]   Combined: {len(combined):,} rows -> " f"{os.path.basename(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
