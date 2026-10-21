import os
import sys

DOCS = [
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs",
]

REQUIRED = [
    "COMPLETE_INSTALLATION_AND_USAGE_GUIDE.pdf",
    "GROQ_API_SETUP_GUIDE.pdf",
    "USER_MANUAL.pdf",
    "DATA_FLOW_AND_IMPLEMENTATION.pdf",
    "SYSTEM_ARCHITECTURE.pdf",
    "SECURITY_ARCHITECTURE.pdf",
    "AI_MODEL_INSTALLATION.pdf",
    "DATASET_GUIDE.pdf",
    "REVIEW_0_PRESENTATION_GUIDE.pdf",
    "PROJECT_FINAL_REPORT.pdf",
]

REQUIRED_PAGES = 1


def verify():
    docs_dir = os.path.join(*DOCS)
    missing = []
    empty = []
    bad = []

    for name in REQUIRED:
        path = os.path.join(docs_dir, name)
        if not os.path.exists(path):
            missing.append(name)
            print("MISSING -", name)
            continue
        size = os.path.getsize(path)
        if size < 500:
            empty.append(name)
            print("EMPTY/TOO SMALL -", name, f"({size} bytes)")
            continue
        try:
            with open(path, "rb") as f:
                head = f.read(1024)
            if b"%PDF" not in head[:5]:
                bad.append(name)
                print("NOT A VALID PDF -", name)
                continue
            print("OK -", name, f"({size} bytes)")
        except Exception as e:
            bad.append(name)
            print("ERROR -", name, str(e))

    if missing or empty or bad:
        print("\nRESULT: FAIL")
        return 1
    print("\nAll required PDFs present and valid.")
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(verify())