# FileCustra Backend Subsystem

The backend architecture consists of two primary components:
1. **Python 3.10 Sidecar (`backend/sidecar/`):** JSON-RPC 2.0 STDIN/STDOUT server handling Google Magika file classification, PyMuPDF/docx text extraction, Tesseract OCR, EmbeddingGemma vector generation, and Gemma ReAct AI topology planning.
2. **Rust Tauri 2 Safe Core (`backend/src-tauri/`):** Privilege-isolated native core handling path canonicalization, SHA-256/xxHash generation, dry-run simulation, and SQLite FTS5 database management.

---

## Directory Breakdown

```
backend/
├── README.md                        # Backend documentation
├── requirements.txt                 # Python sidecar dependencies
├── sidecar/                         # Python JSON-RPC sidecar
│   ├── main.py                      # JSON-RPC STDIN/STDOUT server entrypoint
│   └── requirements.txt             # Pinned sidecar dependencies
└── src-tauri/                       # Tauri 2 Rust Safe Core
    ├── Cargo.toml                   # Rust crate manifest & dependencies
    ├── tauri.conf.json              # Tauri application configuration
    ├── build.rs                     # Tauri build script
    └── src/                         # Rust source files
        ├── lib.rs                   # Core IPC handlers & path canonicalizer
        └── main.rs                  # Native application entrypoint
```

---

## Running Sidecar Standalone

```bash
cd sidecar
python main.py
```
Send JSON-RPC request over STDIN:
```json
{"jsonrpc": "2.0", "method": "magika.classify", "params": {"path": "sample.pdf"}, "id": 1}
```
