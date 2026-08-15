mod database;

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::process::Command as ProcessCommand;
use std::time::{Duration, UNIX_EPOCH};
use walkdir::WalkDir;
use xxhash_rust::xxh64::xxh64;

use database::DatabaseManager;

const BLOCKED_EXTENSIONS: &[&str] = &[
    "exe", "bat", "cmd", "com", "msi", "scr", "pif", "vbs", "vbe", "js", "jse", "ws", "wsc",
    "wsh", "ps1", "psm1", "psd1", "psc1", "reg", "inf",
];

const BLOCKED_DIRECTORIES: &[&str] = &[
    "system32", "syswow64", "windows", "programdata", "recovery",
];

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileMetadata {
    pub path: String,
    pub name: String,
    pub extension: String,
    pub size_bytes: u64,
    pub modified_timestamp: u64,
    pub created_timestamp: u64,
    pub is_directory: bool,
    pub is_readonly: bool,
    pub hash_sha256: Option<String>,
    pub hash_xxh64: Option<u64>,
    pub permissions: FilePermissions,
    pub risk_level: RiskLevel,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FilePermissions {
    pub readable: bool,
    pub writable: bool,
    pub executable: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum RiskLevel {
    Safe,
    Low,
    Medium,
    High,
    Blocked,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScopeConfig {
    pub allowed_roots: Vec<String>,
    pub blocked_paths: Vec<String>,
    pub max_depth: Option<usize>,
    pub include_hidden: bool,
    pub follow_symlinks: bool,
}

impl Default for ScopeConfig {
    fn default() -> Self {
        Self {
            allowed_roots: vec![],
            blocked_paths: vec![],
            max_depth: Some(20),
            include_hidden: false,
            follow_symlinks: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScanResult {
    pub root: String,
    pub files: Vec<FileMetadata>,
    pub directories: Vec<FileMetadata>,
    pub total_files: usize,
    pub total_directories: usize,
    pub total_size_bytes: u64,
    pub errors: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PlannedOperation {
    pub id: String,
    pub source_path: String,
    pub target_path: String,
    pub operation_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ExecutedOperation {
    pub id: String,
    pub source_path: String,
    pub target_path: String,
    pub operation_type: String,
    pub status: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ExecutionJournal {
    pub session_id: String,
    pub root_path: String,
    pub journal_path: String,
    pub timestamp: u64,
    pub operations: Vec<ExecutedOperation>,
}

pub struct FilesystemEngine {
    scope: ScopeConfig,
}

impl FilesystemEngine {
    pub fn new(scope: ScopeConfig) -> Self {
        Self { scope }
    }

    pub fn validate_path(&self, path: &str) -> Result<PathBuf, String> {
        let path = Path::new(path);

        if !path.exists() {
            return Err(format!("Path does not exist: {}", path.display()));
        }

        let canonical = path
            .canonicalize()
            .map_err(|e| format!("Failed to canonicalize path: {}", e))?;

        let canonical_str = canonical.to_string_lossy().to_lowercase();

        if self.is_blocked_path(&canonical_str) {
            return Err(format!("Access denied to blocked path: {}", path.display()));
        }

        if !self.scope.allowed_roots.is_empty() {
            let allowed = self.scope.allowed_roots.iter().any(|root| {
                let root_path = Path::new(root);
                if let Ok(root_canonical) = root_path.canonicalize() {
                    canonical.starts_with(&root_canonical)
                } else {
                    false
                }
            });

            if !allowed {
                return Err(format!(
                    "Path {} is not within allowed scope roots",
                    path.display()
                ));
            }
        }

        Ok(canonical)
    }

    fn is_blocked_path(&self, path: &str) -> bool {
        let path_lower = path.to_lowercase();

        for blocked in &self.scope.blocked_paths {
            if path_lower.contains(&blocked.to_lowercase()) {
                return true;
            }
        }

        let parts: Vec<&str> = path_lower.split(|c| c == '\\' || c == '/').collect();
        for part in parts {
            if BLOCKED_DIRECTORIES.contains(&part) {
                return true;
            }
        }

        false
    }

    pub fn get_file_metadata(&self, path: &str) -> Result<FileMetadata, String> {
        let canonical = self.validate_path(path)?;
        let metadata = fs::metadata(&canonical)
            .map_err(|e| format!("Failed to read file metadata: {}", e))?;

        let extension = canonical
            .extension()
            .and_then(|ext| ext.to_str())
            .unwrap_or("")
            .to_string();

        let name = canonical
            .file_name()
            .and_then(|name| name.to_str())
            .unwrap_or("")
            .to_string();

        let modified = metadata
            .modified()
            .map(|t| t.duration_since(UNIX_EPOCH).unwrap_or(Duration::ZERO).as_secs())
            .unwrap_or(0);

        let created = metadata
            .created()
            .map(|t| t.duration_since(UNIX_EPOCH).unwrap_or(Duration::ZERO).as_secs())
            .unwrap_or(0);

        let permissions = FilePermissions {
            readable: true,
            writable: !metadata.permissions().readonly(),
            executable: !metadata.permissions().readonly(),
        };

        let risk_level = self.assess_risk(&extension, &canonical);

        Ok(FileMetadata {
            path: canonical.to_string_lossy().to_string(),
            name,
            extension,
            size_bytes: metadata.len(),
            modified_timestamp: modified,
            created_timestamp: created,
            is_directory: metadata.is_dir(),
            is_readonly: metadata.permissions().readonly(),
            hash_sha256: None,
            hash_xxh64: None,
            permissions,
            risk_level,
        })
    }

    fn assess_risk(&self, extension: &str, path: &Path) -> RiskLevel {
        let ext_lower = extension.to_lowercase();

        if BLOCKED_EXTENSIONS.contains(&ext_lower.as_str()) {
            return RiskLevel::Blocked;
        }

        let path_str = path.to_string_lossy().to_lowercase();
        if path_str.contains("\\appdata\\") || path_str.contains("\\temp\\") {
            return RiskLevel::Medium;
        }

        match ext_lower.as_str() {
            "pdf" | "doc" | "docx" | "xls" | "xlsx" | "ppt" | "pptx" => RiskLevel::Safe,
            "txt" | "md" | "json" | "xml" | "csv" | "log" => RiskLevel::Safe,
            "rs" | "py" | "js" | "ts" | "jsx" | "tsx" | "java" | "cpp" | "c" | "h" => RiskLevel::Safe,
            "png" | "jpg" | "jpeg" | "gif" | "bmp" | "webp" | "svg" => RiskLevel::Safe,
            "mp3" | "wav" | "flac" | "ogg" | "aac" => RiskLevel::Safe,
            "mp4" | "avi" | "mkv" | "mov" | "wmv" | "webm" => RiskLevel::Safe,
            "zip" | "rar" | "7z" | "tar" | "gz" => RiskLevel::Low,
            "dll" | "sys" | "drv" | "ocx" => RiskLevel::Medium,
            "tmp" | "temp" | "bak" | "old" => RiskLevel::Low,
            "" => RiskLevel::Low,
            _ => RiskLevel::Safe,
        }
    }

    pub fn hash_file_sha256(&self, path: &str) -> Result<String, String> {
        let canonical = self.validate_path(path)?;

        if !canonical.exists() {
            return Err(format!("File does not exist: {}", path));
        }

        let mut file = fs::File::open(&canonical)
            .map_err(|e| format!("Failed to open file for hashing: {}", e))?;

        let mut hasher = Sha256::new();
        let mut buffer = [0u8; 8192];

        loop {
            let bytes_read = std::io::Read::read(&mut file, &mut buffer)
                .map_err(|e| format!("Failed to read file for hashing: {}", e))?;

            if bytes_read == 0 {
                break;
            }

            hasher.update(&buffer[..bytes_read]);
        }

        Ok(format!("{:x}", hasher.finalize()))
    }

    pub fn hash_file_xxh64(&self, path: &str) -> Result<u64, String> {
        let canonical = self.validate_path(path)?;

        if !canonical.exists() {
            return Err(format!("File does not exist: {}", path));
        }

        let content = fs::read(&canonical)
            .map_err(|e| format!("Failed to read file for hashing: {}", e))?;

        Ok(xxh64(&content, 0))
    }

    pub fn scan_directory(&self, path: &str, depth: usize) -> Result<ScanResult, String> {
        let canonical = self.validate_path(path)?;

        if !canonical.is_dir() {
            return Err(format!("Path is not a directory: {}", path));
        }

        let mut files = Vec::new();
        let mut directories = Vec::new();
        let mut total_size = 0u64;
        let mut errors = Vec::new();

        let walker = WalkDir::new(&canonical)
            .max_depth(depth.min(self.scope.max_depth.unwrap_or(20)))
            .follow_links(self.scope.follow_symlinks)
            .into_iter();

        for entry in walker {
            match entry {
                Ok(entry) => {
                    let entry_path = entry.path();

                    if entry.file_type().is_symlink() {
                        errors.push(format!(
                            "Symlink/junction skipped without following target: {}",
                            entry_path.display()
                        ));
                        continue;
                    }

                    if !self.scope.include_hidden {
                        if let Some(name) = entry_path.file_name() {
                            if name.to_string_lossy().starts_with('.') {
                                continue;
                            }
                        }
                    }

                    let path_str = entry_path.to_string_lossy().to_string();
                    match self.get_file_metadata(&path_str) {
                        Ok(metadata) => {
                            if metadata.is_directory {
                                directories.push(metadata);
                            } else {
                                let mut file_metadata = metadata;
                                match self.hash_file_sha256(&path_str) {
                                    Ok(hash) => file_metadata.hash_sha256 = Some(hash),
                                    Err(e) => errors.push(format!("Hash SHA-256 error for {}: {}", path_str, e)),
                                }
                                match self.hash_file_xxh64(&path_str) {
                                    Ok(hash) => file_metadata.hash_xxh64 = Some(hash),
                                    Err(e) => errors.push(format!("Hash xxh64 error for {}: {}", path_str, e)),
                                }
                                total_size += file_metadata.size_bytes;
                                files.push(file_metadata);
                            }
                        }
                        Err(e) => {
                            errors.push(format!("{}: {}", path_str, e));
                        }
                    }
                }
                Err(e) => {
                    errors.push(format!("Walk error: {}", e));
                }
            }
        }

        let total_files = files.len();
        let total_directories = directories.len();

        Ok(ScanResult {
            root: canonical.to_string_lossy().to_string(),
            total_files,
            total_directories,
            total_size_bytes: total_size,
            files,
            directories,
            errors,
        })
    }

    pub fn compute_file_hashes(&self, path: &str) -> Result<FileMetadata, String> {
        let mut metadata = self.get_file_metadata(path)?;

        if !metadata.is_directory {
            metadata.hash_sha256 = Some(self.hash_file_sha256(path)?);
            metadata.hash_xxh64 = Some(self.hash_file_xxh64(path)?);
        }

        Ok(metadata)
    }
}

#[tauri::command]
fn canonicalize_and_scope_path(raw_path: String) -> Result<String, String> {
    let engine = FilesystemEngine::new(ScopeConfig::default());
    let canonical = engine.validate_path(&raw_path)?;
    Ok(canonical.to_string_lossy().to_string())
}

#[tauri::command]
fn get_file_metadata(path: String) -> Result<FileMetadata, String> {
    let engine = FilesystemEngine::new(ScopeConfig::default());
    engine.get_file_metadata(&path)
}

#[tauri::command]
fn scan_directory(path: String, max_depth: Option<usize>, include_hidden: Option<bool>) -> Result<ScanResult, String> {
    let scope = ScopeConfig {
        max_depth,
        include_hidden: include_hidden.unwrap_or(false),
        ..Default::default()
    };
    let engine = FilesystemEngine::new(scope);
    engine.scan_directory(&path, max_depth.unwrap_or(10))
}

#[tauri::command]
fn compute_file_hash(path: String, algorithm: Option<String>) -> Result<String, String> {
    let engine = FilesystemEngine::new(ScopeConfig::default());
    match algorithm.as_deref() {
        Some("xxh64") => {
            let hash = engine.hash_file_xxh64(&path)?;
            Ok(format!("{:016x}", hash))
        }
        _ => engine.hash_file_sha256(&path),
    }
}

#[tauri::command]
fn compute_file_hashes(path: String) -> Result<FileMetadata, String> {
    let engine = FilesystemEngine::new(ScopeConfig::default());
    engine.compute_file_hashes(&path)
}

fn reject_parent_components(path: &Path) -> Result<(), String> {
    for component in path.components() {
        if matches!(component, Component::ParentDir | Component::Prefix(_) | Component::RootDir) {
            return Err(format!(
                "Target path must be relative to the selected workspace: {}",
                path.display()
            ));
        }
    }
    Ok(())
}

fn unique_target_path(target: &Path) -> PathBuf {
    if !target.exists() {
        return target.to_path_buf();
    }

    let parent = target.parent().unwrap_or_else(|| Path::new(""));
    let stem = target
        .file_stem()
        .and_then(|value| value.to_str())
        .unwrap_or("file");
    let extension = target.extension().and_then(|value| value.to_str());

    for index in 1..10_000 {
        let file_name = match extension {
            Some(ext) if !ext.is_empty() => format!("{}_{}.{}", stem, index, ext),
            _ => format!("{}_{}", stem, index),
        };
        let candidate = parent.join(file_name);
        if !candidate.exists() {
            return candidate;
        }
    }

    target.to_path_buf()
}

fn unix_timestamp() -> u64 {
    std::time::SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or(Duration::ZERO)
        .as_secs()
}

fn journal_session_id() -> String {
    let millis = std::time::SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or(Duration::ZERO)
        .as_millis();
    format!("sess-{}", millis)
}

#[tauri::command]
fn execute_operation_plan(
    root_path: String,
    operations: Vec<PlannedOperation>,
) -> Result<ExecutionJournal, String> {
    let engine = FilesystemEngine::new(ScopeConfig::default());
    let root = engine.validate_path(&root_path)?;

    if operations.is_empty() {
        return Err("No operations were supplied for execution".to_string());
    }

    let session_id = journal_session_id();
    let mut executed = Vec::new();

    for operation in operations {
        if operation.operation_type != "MOVE" {
            return Err(format!(
                "Unsupported operation type for real execution: {}",
                operation.operation_type
            ));
        }

        let source = engine.validate_path(&operation.source_path)?;
        if !source.starts_with(&root) {
            return Err(format!(
                "Source file is outside the selected workspace: {}",
                source.display()
            ));
        }

        if !source.is_file() {
            return Err(format!("Source is not a file: {}", source.display()));
        }

        let relative_target = Path::new(&operation.target_path);
        reject_parent_components(relative_target)?;
        let target = root.join(relative_target);
        if !target.starts_with(&root) {
            return Err(format!(
                "Target path escaped the selected workspace: {}",
                target.display()
            ));
        }

        if let Some(parent) = target.parent() {
            fs::create_dir_all(parent)
                .map_err(|e| format!("Failed to create target directory {}: {}", parent.display(), e))?;
        }

        let final_target = unique_target_path(&target);
        fs::rename(&source, &final_target).map_err(|e| {
            format!(
                "Failed to move {} to {}: {}",
                source.display(),
                final_target.display(),
                e
            )
        })?;

        executed.push(ExecutedOperation {
            id: operation.id,
            source_path: source.to_string_lossy().to_string(),
            target_path: final_target.to_string_lossy().to_string(),
            operation_type: operation.operation_type,
            status: "COMPLETED".to_string(),
        });
    }

    let journal_dir = root.join(".filecustra_journal");
    fs::create_dir_all(&journal_dir).map_err(|e| {
        format!(
            "Failed to create rollback journal directory {}: {}",
            journal_dir.display(),
            e
        )
    })?;

    let journal_path = journal_dir.join(format!("{}.json", session_id));
    let journal = ExecutionJournal {
        session_id,
        root_path: root.to_string_lossy().to_string(),
        journal_path: journal_path.to_string_lossy().to_string(),
        timestamp: unix_timestamp(),
        operations: executed,
    };

    let payload = serde_json::to_string_pretty(&journal)
        .map_err(|e| format!("Failed to serialize rollback journal: {}", e))?;
    fs::write(&journal_path, payload)
        .map_err(|e| format!("Failed to write rollback journal {}: {}", journal_path.display(), e))?;

    Ok(journal)
}

#[tauri::command]
fn rollback_operation_journal(journal_path: String) -> Result<ExecutionJournal, String> {
    let payload = fs::read_to_string(&journal_path)
        .map_err(|e| format!("Failed to read rollback journal {}: {}", journal_path, e))?;
    let mut journal: ExecutionJournal = serde_json::from_str(&payload)
        .map_err(|e| format!("Failed to parse rollback journal: {}", e))?;

    for operation in journal.operations.iter_mut().rev() {
        if operation.status == "ROLLED_BACK" {
            continue;
        }

        let current = Path::new(&operation.target_path);
        let original = Path::new(&operation.source_path);

        if !current.exists() {
            operation.status = "MISSING_TARGET".to_string();
            continue;
        }

        if let Some(parent) = original.parent() {
            fs::create_dir_all(parent).map_err(|e| {
                format!(
                    "Failed to recreate original directory {}: {}",
                    parent.display(),
                    e
                )
            })?;
        }

        let final_original = unique_target_path(original);
        fs::rename(current, &final_original).map_err(|e| {
            format!(
                "Failed to roll back {} to {}: {}",
                current.display(),
                final_original.display(),
                e
            )
        })?;

        operation.status = "ROLLED_BACK".to_string();
    }

    let updated_payload = serde_json::to_string_pretty(&journal)
        .map_err(|e| format!("Failed to serialize updated rollback journal: {}", e))?;
    fs::write(&journal_path, updated_payload)
        .map_err(|e| format!("Failed to update rollback journal {}: {}", journal_path, e))?;

    Ok(journal)
}

#[tauri::command]
fn check_hardware_capabilities() -> Result<String, String> {
    Ok("NVIDIA RTX / DirectML VRAM 4GB+ Detected - LiteRT-LM Active".into())
}

/// Finds the project's dedicated "filecustra" conda environment's Python
/// interpreter. This project intentionally runs its Python backend only from
/// that environment - not a bare `python`/`py`/`python3` on PATH, which is
/// unreliable on Windows (resolves to whatever happens to be first on PATH,
/// e.g. the Windows Store alias stub with none of the sidecar's real
/// dependencies installed) and was the source of earlier "Scan failed"
/// errors. Create the environment with:
///   conda create -n filecustra python=3.10
///   conda run -n filecustra pip install -r backend/requirements.txt
fn resolve_python_command() -> Option<String> {
    let user_profile = std::env::var("USERPROFILE").ok()?;
    for conda_root in ["anaconda3", "miniconda3"] {
        let candidate = Path::new(&user_profile)
            .join(conda_root)
            .join("envs")
            .join("filecustra")
            .join("python.exe");
        if candidate.exists() {
            return Some(candidate.to_string_lossy().to_string());
        }
    }
    None
}

/// Runs the Gemma-voiced structural report composer (`backend/sidecar/scan_report.py`)
/// against a compact scan summary built from a real `scan_directory` result. The
/// Python sidecar owns the product's reasoning/rationale voice, so this shells out
/// to it as a one-shot subprocess rather than duplicating the composition in Rust.
#[tauri::command]
fn generate_topology_report(payload: String) -> Result<String, String> {
    let script_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("sidecar")
        .join("scan_report.py");

    if !script_path.exists() {
        return Err(format!(
            "Gemma report script not found at {}",
            script_path.display()
        ));
    }

    let python_cmd = resolve_python_command().ok_or_else(|| {
        "The 'filecustra' conda environment was not found. Create it with: conda create -n filecustra python=3.10, then: conda run -n filecustra pip install -r backend/requirements.txt".to_string()
    })?;

    let output = ProcessCommand::new(python_cmd)
        .arg(&script_path)
        .arg(&payload)
        .output()
        .map_err(|e| format!("Failed to launch the Gemma report process: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        return Err(format!(
            "Gemma report process exited with an error: {}",
            if stderr.is_empty() { "unknown error".to_string() } else { stderr }
        ));
    }

    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

/// Runs at app load (see `SplashView.tsx`) to report real backend readiness -
/// Python interpreter, required libraries, local model files, and Tesseract -
/// instead of the app silently failing later on the first real action.
#[tauri::command]
fn check_runtime_readiness() -> Result<String, String> {
    let script_path = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("..")
        .join("sidecar")
        .join("runtime_readiness.py");

    let python_cmd = match resolve_python_command() {
        Some(cmd) => cmd,
        None => {
            return Ok(
                "{\"pythonAvailable\":false,\"pythonError\":\"The 'filecustra' conda environment was not found. Create it with: conda create -n filecustra python=3.10, then: conda run -n filecustra pip install -r backend/requirements.txt\",\"libraries\":[],\"models\":[],\"tesseract\":{\"available\":false,\"path\":null}}"
                    .to_string(),
            );
        }
    };

    if !script_path.exists() {
        return Err(format!(
            "Runtime readiness script not found at {}",
            script_path.display()
        ));
    }

    let output = ProcessCommand::new(python_cmd)
        .arg(&script_path)
        .output()
        .map_err(|e| format!("Failed to launch the runtime readiness process: {}", e))?;

    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).trim().to_string();
        return Err(format!(
            "Runtime readiness process exited with an error: {}",
            if stderr.is_empty() { "unknown error".to_string() } else { stderr }
        ));
    }

    Ok(String::from_utf8_lossy(&output.stdout).trim().to_string())
}

#[tauri::command]
fn db_create_session(db_path: String, name: String, root_path: String) -> Result<i64, String> {
    let db = DatabaseManager::new(Path::new(&db_path))
        .map_err(|e| format!("Database error: {}", e))?;
    db.create_session(&name, &root_path)
        .map_err(|e| format!("Session creation error: {}", e))
}

#[tauri::command]
fn db_get_session(db_path: String, session_id: i64) -> Result<Option<database::Session>, String> {
    let db = DatabaseManager::new(Path::new(&db_path))
        .map_err(|e| format!("Database error: {}", e))?;
    db.get_session(session_id)
        .map_err(|e| format!("Session query error: {}", e))
}

#[tauri::command]
fn db_list_sessions(db_path: String) -> Result<Vec<database::Session>, String> {
    let db = DatabaseManager::new(Path::new(&db_path))
        .map_err(|e| format!("Database error: {}", e))?;
    db.list_sessions()
        .map_err(|e| format!("Session list error: {}", e))
}

#[tauri::command]
fn db_search_files(db_path: String, session_id: i64, query: String) -> Result<Vec<database::FileSnapshot>, String> {
    let db = DatabaseManager::new(Path::new(&db_path))
        .map_err(|e| format!("Database error: {}", e))?;
    db.search_files(session_id, &query)
        .map_err(|e| format!("File search error: {}", e))
}

#[tauri::command]
fn db_set_user_preference(db_path: String, key: String, value: String, category: String) -> Result<(), String> {
    let db = DatabaseManager::new(Path::new(&db_path))
        .map_err(|e| format!("Database error: {}", e))?;
    db.set_user_preference(&key, &value, &category)
        .map_err(|e| format!("Preference set error: {}", e))
}

#[tauri::command]
fn db_get_user_preference(db_path: String, key: String) -> Result<Option<String>, String> {
    let db = DatabaseManager::new(Path::new(&db_path))
        .map_err(|e| format!("Database error: {}", e))?;
    db.get_user_preference(&key)
        .map_err(|e| format!("Preference get error: {}", e))
}

#[tauri::command]
fn db_get_installed_models(db_path: String) -> Result<Vec<database::InstalledModel>, String> {
    let db = DatabaseManager::new(Path::new(&db_path))
        .map_err(|e| format!("Database error: {}", e))?;
    db.get_installed_models()
        .map_err(|e| format!("Model list error: {}", e))
}

pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            canonicalize_and_scope_path,
            get_file_metadata,
            scan_directory,
            compute_file_hash,
            compute_file_hashes,
            execute_operation_plan,
            rollback_operation_journal,
            check_hardware_capabilities,
            generate_topology_report,
            check_runtime_readiness,
            db_create_session,
            db_get_session,
            db_list_sessions,
            db_search_files,
            db_set_user_preference,
            db_get_user_preference,
            db_get_installed_models,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs::File;
    use std::io::Write;
    use tempfile::TempDir;

    fn create_test_file(dir: &Path, name: &str, content: &[u8]) -> PathBuf {
        let path = dir.join(name);
        let mut file = File::create(&path).unwrap();
        file.write_all(content).unwrap();
        path
    }

    #[test]
    fn test_validate_path_valid() {
        let temp_dir = TempDir::new().unwrap();
        let engine = FilesystemEngine::new(ScopeConfig::default());
        let path = create_test_file(temp_dir.path(), "test.txt", b"hello");
        let result = engine.validate_path(&path.to_string_lossy());
        assert!(result.is_ok());
    }

    #[test]
    fn test_validate_path_nonexistent() {
        let engine = FilesystemEngine::new(ScopeConfig::default());
        let result = engine.validate_path("C:\\nonexistent\\path\\file.txt");
        assert!(result.is_err());
    }

    #[test]
    fn test_is_blocked_path_system32() {
        let engine = FilesystemEngine::new(ScopeConfig::default());
        assert!(engine.is_blocked_path("C:\\Windows\\System32\\test.dll"));
        assert!(engine.is_blocked_path("C:\\WINDOWS\\system32\\drivers\\test.sys"));
    }

    #[test]
    fn test_assess_risk_safe() {
        let engine = FilesystemEngine::new(ScopeConfig::default());
        assert!(matches!(
            engine.assess_risk("txt", Path::new("test.txt")),
            RiskLevel::Safe
        ));
        assert!(matches!(
            engine.assess_risk("pdf", Path::new("doc.pdf")),
            RiskLevel::Safe
        ));
    }

    #[test]
    fn test_assess_risk_blocked() {
        let engine = FilesystemEngine::new(ScopeConfig::default());
        assert!(matches!(
            engine.assess_risk("exe", Path::new("malware.exe")),
            RiskLevel::Blocked
        ));
        assert!(matches!(
            engine.assess_risk("bat", Path::new("script.bat")),
            RiskLevel::Blocked
        ));
    }

    #[test]
    fn test_hash_file_sha256() {
        let temp_dir = TempDir::new().unwrap();
        let path = create_test_file(temp_dir.path(), "hash_test.txt", b"test content");
        let engine = FilesystemEngine::new(ScopeConfig::default());
        let hash = engine.hash_file_sha256(&path.to_string_lossy()).unwrap();
        assert!(!hash.is_empty());
        assert_eq!(hash.len(), 64);
    }

    #[test]
    fn test_hash_file_xxh64() {
        let temp_dir = TempDir::new().unwrap();
        let path = create_test_file(temp_dir.path(), "hash_test.txt", b"test content");
        let engine = FilesystemEngine::new(ScopeConfig::default());
        let hash = engine.hash_file_xxh64(&path.to_string_lossy()).unwrap();
        assert!(hash > 0);
    }

    #[test]
    fn test_get_file_metadata() {
        let temp_dir = TempDir::new().unwrap();
        let path = create_test_file(temp_dir.path(), "meta_test.txt", b"test content");
        let engine = FilesystemEngine::new(ScopeConfig::default());
        let metadata = engine.get_file_metadata(&path.to_string_lossy()).unwrap();
        assert_eq!(metadata.name, "meta_test.txt");
        assert_eq!(metadata.extension, "txt");
        assert_eq!(metadata.size_bytes, 12);
        assert!(!metadata.is_directory);
    }

    #[test]
    fn test_scan_directory() {
        let temp_dir = TempDir::new().unwrap();
        create_test_file(temp_dir.path(), "file1.txt", b"content1");
        create_test_file(temp_dir.path(), "file2.txt", b"content2");

        let sub_dir = temp_dir.path().join("subdir");
        fs::create_dir(&sub_dir).unwrap();
        create_test_file(&sub_dir, "file3.txt", b"content3");

        let engine = FilesystemEngine::new(ScopeConfig::default());
        let result = engine
            .scan_directory(&temp_dir.path().to_string_lossy(), 10)
            .unwrap();

        assert_eq!(result.files.len(), 3);
        assert_eq!(result.directories.len(), 1);
        assert!(result.total_size_bytes > 0);
    }

    #[test]
    fn test_scope_restriction() {
        let temp_dir = TempDir::new().unwrap();
        let allowed_dir = temp_dir.path().join("allowed");
        let blocked_dir = temp_dir.path().join("blocked");
        fs::create_dir(&allowed_dir).unwrap();
        fs::create_dir(&blocked_dir).unwrap();

        let scope = ScopeConfig {
            allowed_roots: vec![allowed_dir.to_string_lossy().to_string()],
            ..Default::default()
        };

        let engine = FilesystemEngine::new(scope);
        let allowed_file = create_test_file(&allowed_dir, "test.txt", b"ok");
        let blocked_file = create_test_file(&blocked_dir, "test.txt", b"no");

        assert!(engine.validate_path(&allowed_file.to_string_lossy()).is_ok());
        assert!(engine.validate_path(&blocked_file.to_string_lossy()).is_err());
    }

    #[test]
    fn test_execute_operation_plan_moves_real_file_and_rolls_back() {
        let temp_dir = TempDir::new().unwrap();
        let source = create_test_file(temp_dir.path(), "report.txt", b"content");

        let journal = execute_operation_plan(
            temp_dir.path().to_string_lossy().to_string(),
            vec![PlannedOperation {
                id: "op-1".to_string(),
                source_path: source.to_string_lossy().to_string(),
                target_path: "Projects/Text/report.txt".to_string(),
                operation_type: "MOVE".to_string(),
            }],
        )
        .unwrap();

        let moved = temp_dir.path().join("Projects").join("Text").join("report.txt");
        assert!(!source.exists());
        assert!(moved.exists());
        assert!(Path::new(&journal.journal_path).exists());
        assert_eq!(journal.operations[0].status, "COMPLETED");

        let rolled_back = rollback_operation_journal(journal.journal_path).unwrap();
        assert!(source.exists());
        assert!(!moved.exists());
        assert_eq!(rolled_back.operations[0].status, "ROLLED_BACK");
    }

    #[test]
    fn test_execute_operation_plan_rejects_target_traversal() {
        let temp_dir = TempDir::new().unwrap();
        let source = create_test_file(temp_dir.path(), "report.txt", b"content");

        let result = execute_operation_plan(
            temp_dir.path().to_string_lossy().to_string(),
            vec![PlannedOperation {
                id: "op-1".to_string(),
                source_path: source.to_string_lossy().to_string(),
                target_path: "../outside/report.txt".to_string(),
                operation_type: "MOVE".to_string(),
            }],
        );

        assert!(result.is_err());
        assert!(source.exists());
    }

    #[test]
    fn test_database_integration() {
        let db = DatabaseManager::new_in_memory().unwrap();
        let session_id = db.create_session("Test Integration", "/test").unwrap();
        assert!(session_id > 0);

        let session = db.get_session(session_id).unwrap().unwrap();
        assert_eq!(session.name, "Test Integration");
    }
}
