#!/usr/bin/env python3
import sys
import json


def main():
    data = json.load(sys.stdin)
    if data.get("tool_name") not in ("Write", "Edit", "MultiEdit"):
        print(json.dumps({}))
        sys.exit(0)

    file_path = data.get("file_path", "")
    if not file_path.endswith(".py"):
        print(json.dumps({}))
        sys.exit(0)

    msg = (
        f"Python file just written: {file_path}. "
        "Spawn a fork sub-agent to review it for idiomatic Python and security issues "
        "(timeouts on network calls, lazy init with lru_cache, guard clauses, "
        "public-before-private ordering). Report findings as a prioritized table."
    )
    print(json.dumps({"systemMessage": msg}))
    sys.exit(0)


if __name__ == "__main__":
    main()
