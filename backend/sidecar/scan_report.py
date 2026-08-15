#!/usr/bin/env python3
"""Gemma-voiced structural report composer.

Takes a compact JSON scan summary (produced by the Rust filesystem engine
after a real `scan_directory` call) as argv[1] and prints a multi-paragraph,
plain-text structural report to stdout. This is invoked directly by the
Tauri backend as a one-shot subprocess per scan, not through the persistent
JSON-RPC sidecar loop in main.py.
"""

import json
import sys
from typing import Any, Dict, List


def format_size(num_bytes: float) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


def build_report(summary: Dict[str, Any]) -> str:
    root = summary.get("root") or "the selected workspace"
    total_files = int(summary.get("totalFiles", 0))
    total_directories = int(summary.get("totalDirectories", 0))
    total_size = summary.get("totalSizeBytes", 0)
    subfolders: List[Dict[str, Any]] = summary.get("subfolders", []) or []
    top_extensions: List[Dict[str, Any]] = summary.get("topExtensions", []) or []
    scan_depth = summary.get("scanDepth")

    paragraphs = []

    depth_note = f" (scanned {scan_depth} folder levels deep)" if scan_depth else ""
    paragraphs.append(
        f"Gemma scanned {root} in read-only mode{depth_note} and found {total_files} "
        f"file{'s' if total_files != 1 else ''} across {total_directories} "
        f"folder{'s' if total_directories != 1 else ''}, totaling {format_size(total_size)}."
    )

    if total_files == 0:
        paragraphs.append(
            "No files were detected at this scan depth. Try a shallower folder, increase the "
            "scan depth, or confirm the workspace path is correct."
        )
    else:
        if subfolders:
            ranked = sorted(subfolders, key=lambda s: s.get("fileCount", 0), reverse=True)
            top = ranked[:5]
            folder_desc = ", ".join(f"{s.get('name', 'Unnamed')} ({s.get('fileCount', 0)} files)" for s in top)
            paragraphs.append(
                f"The largest concentrations of content sit in {folder_desc}. These will anchor "
                "the fuzzy cluster groups shown in the topology web below."
            )
        else:
            paragraphs.append(
                "All detected files sit directly at the root of this folder, so no subfolder "
                "clustering was needed for this pass."
            )

        if top_extensions:
            ext_desc = ", ".join(
                f"{(e.get('extension') or 'no-extension')} x{e.get('count', 0)}" for e in top_extensions[:5]
            )
            paragraphs.append(f"By format, the workspace is dominated by {ext_desc}.")

        if total_directories > 12:
            paragraphs.append(
                "Folder depth and spread here are high enough that a manual pass would be slow. "
                "This is a strong candidate for an automated structure plan in the next step."
            )
        elif total_directories <= 1 and total_files > 8:
            paragraphs.append(
                "Nearly everything is sitting flat in one folder. Grouping by format or project "
                "would meaningfully cut down browsing time here."
            )
        else:
            paragraphs.append(
                "This workspace is compact enough to review by hand, but a structure plan can "
                "still tidy naming and grouping in one pass."
            )

    paragraphs.append(
        "No files have been moved, renamed, or modified. This report is read-only until a "
        "structure plan is generated and you approve a dry run."
    )

    return "\n\n".join(paragraphs)


def main() -> None:
    if len(sys.argv) < 2:
        print("Gemma report error: missing scan summary payload.", file=sys.stderr)
        sys.exit(1)

    try:
        summary = json.loads(sys.argv[1])
    except json.JSONDecodeError as exc:
        print(f"Gemma report error: invalid scan summary JSON ({exc}).", file=sys.stderr)
        sys.exit(1)

    sys.stdout.write(build_report(summary))


if __name__ == "__main__":
    main()
