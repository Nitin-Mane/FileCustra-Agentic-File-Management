use rusqlite::{Connection, Result as SqlResult, params};
use serde::{Deserialize, Serialize};
use std::path::Path;
use std::sync::Mutex;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub id: i64,
    pub name: String,
    pub created_at: String,
    pub updated_at: String,
    pub status: String,
    pub root_path: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileSnapshot {
    pub id: i64,
    pub session_id: i64,
    pub file_path: String,
    pub file_name: String,
    pub extension: String,
    pub size_bytes: u64,
    pub hash_sha256: Option<String>,
    pub hash_xxh64: Option<u64>,
    pub modified_timestamp: u64,
    pub created_timestamp: u64,
    pub is_directory: bool,
    pub risk_level: String,
    pub content_text: Option<String>,
    pub indexed_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AnalysisResult {
    pub id: i64,
    pub session_id: i64,
    pub file_id: i64,
    pub analysis_type: String,
    pub result_json: String,
    pub confidence: f64,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OperationPlan {
    pub id: i64,
    pub session_id: i64,
    pub strategy: String,
    pub plan_json: String,
    pub status: String,
    pub created_at: String,
    pub executed_at: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JournalEntry {
    pub id: i64,
    pub session_id: i64,
    pub operation_id: String,
    pub operation_type: String,
    pub source_path: String,
    pub target_path: Option<String>,
    pub status: String,
    pub created_at: String,
    pub completed_at: Option<String>,
    pub error_message: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UserPreference {
    pub id: i64,
    pub key: String,
    pub value: String,
    pub category: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InstalledModel {
    pub id: i64,
    pub model_name: String,
    pub model_version: String,
    pub model_path: String,
    pub model_type: String,
    pub size_bytes: u64,
    pub hash_sha256: Option<String>,
    pub installed_at: String,
    pub last_used_at: Option<String>,
}

pub struct DatabaseManager {
    conn: Mutex<Connection>,
}

impl DatabaseManager {
    pub fn new(db_path: &Path) -> SqlResult<Self> {
        let conn = Connection::open(db_path)?;
        let manager = Self {
            conn: Mutex::new(conn),
        };
        manager.run_migrations()?;
        Ok(manager)
    }

    pub fn new_in_memory() -> SqlResult<Self> {
        let conn = Connection::open_in_memory()?;
        let manager = Self {
            conn: Mutex::new(conn),
        };
        manager.run_migrations()?;
        Ok(manager)
    }

    fn run_migrations(&self) -> SqlResult<()> {
        let conn = self.conn.lock().unwrap();

        conn.execute_batch("PRAGMA journal_mode=WAL;")?;
        conn.execute_batch("PRAGMA foreign_keys=ON;")?;

        conn.execute_batch("
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                status TEXT NOT NULL DEFAULT 'active',
                root_path TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS file_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                extension TEXT NOT NULL DEFAULT '',
                size_bytes INTEGER NOT NULL DEFAULT 0,
                hash_sha256 TEXT,
                hash_xxh64 INTEGER,
                modified_timestamp INTEGER NOT NULL DEFAULT 0,
                created_timestamp INTEGER NOT NULL DEFAULT 0,
                is_directory INTEGER NOT NULL DEFAULT 0,
                risk_level TEXT NOT NULL DEFAULT 'safe',
                content_text TEXT,
                indexed_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS analysis_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                file_id INTEGER NOT NULL,
                analysis_type TEXT NOT NULL,
                result_json TEXT NOT NULL,
                confidence REAL NOT NULL DEFAULT 0.0,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES file_snapshots(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS operation_plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                strategy TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                executed_at TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                operation_id TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                source_path TEXT NOT NULL,
                target_path TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                completed_at TEXT,
                error_message TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS user_preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key TEXT NOT NULL UNIQUE,
                value TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'general',
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS installed_models (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                model_version TEXT NOT NULL DEFAULT '1.0.0',
                model_path TEXT NOT NULL,
                model_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL DEFAULT 0,
                hash_sha256 TEXT,
                installed_at TEXT NOT NULL DEFAULT (datetime('now')),
                last_used_at TEXT
            );
        ")?;

        conn.execute_batch("
            CREATE INDEX IF NOT EXISTS idx_file_snapshots_session ON file_snapshots(session_id);
            CREATE INDEX IF NOT EXISTS idx_file_snapshots_path ON file_snapshots(file_path);
            CREATE INDEX IF NOT EXISTS idx_file_snapshots_name ON file_snapshots(file_name);
            CREATE INDEX IF NOT EXISTS idx_analysis_results_session ON analysis_results(session_id);
            CREATE INDEX IF NOT EXISTS idx_analysis_results_file ON analysis_results(file_id);
            CREATE INDEX IF NOT EXISTS idx_operation_plans_session ON operation_plans(session_id);
            CREATE INDEX IF NOT EXISTS idx_journal_session ON journal(session_id);
            CREATE INDEX IF NOT EXISTS idx_journal_operation ON journal(operation_id);
            CREATE INDEX IF NOT EXISTS idx_user_preferences_key ON user_preferences(key);
            CREATE INDEX IF NOT EXISTS idx_installed_models_name ON installed_models(model_name);
        ")?;

        Ok(())
    }

    pub fn create_session(&self, name: &str, root_path: &str) -> SqlResult<i64> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO sessions (name, root_path) VALUES (?1, ?2)",
            params![name, root_path],
        )?;
        Ok(conn.last_insert_rowid())
    }

    pub fn get_session(&self, id: i64) -> SqlResult<Option<Session>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, name, created_at, updated_at, status, root_path FROM sessions WHERE id = ?1"
        )?;
        let mut rows = stmt.query_map(params![id], |row| {
            Ok(Session {
                id: row.get(0)?,
                name: row.get(1)?,
                created_at: row.get(2)?,
                updated_at: row.get(3)?,
                status: row.get(4)?,
                root_path: row.get(5)?,
            })
        })?;
        match rows.next() {
            Some(row) => Ok(Some(row?)),
            None => Ok(None),
        }
    }

    pub fn list_sessions(&self) -> SqlResult<Vec<Session>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, name, created_at, updated_at, status, root_path FROM sessions ORDER BY created_at DESC"
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(Session {
                id: row.get(0)?,
                name: row.get(1)?,
                created_at: row.get(2)?,
                updated_at: row.get(3)?,
                status: row.get(4)?,
                root_path: row.get(5)?,
            })
        })?;
        let mut sessions = Vec::new();
        for row in rows {
            sessions.push(row?);
        }
        Ok(sessions)
    }

    pub fn insert_file_snapshot(&self, snapshot: &FileSnapshot) -> SqlResult<i64> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO file_snapshots (session_id, file_path, file_name, extension, size_bytes, hash_sha256, hash_xxh64, modified_timestamp, created_timestamp, is_directory, risk_level, content_text) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)",
            params![
                snapshot.session_id,
                snapshot.file_path,
                snapshot.file_name,
                snapshot.extension,
                snapshot.size_bytes,
                snapshot.hash_sha256,
                snapshot.hash_xxh64,
                snapshot.modified_timestamp,
                snapshot.created_timestamp,
                snapshot.is_directory,
                snapshot.risk_level,
                snapshot.content_text,
            ],
        )?;
        Ok(conn.last_insert_rowid())
    }

    pub fn search_files(&self, session_id: i64, query: &str) -> SqlResult<Vec<FileSnapshot>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, session_id, file_path, file_name, extension, size_bytes, hash_sha256, hash_xxh64, modified_timestamp, created_timestamp, is_directory, risk_level, content_text, indexed_at FROM file_snapshots WHERE session_id = ?1 AND (file_name LIKE ?2 OR content_text LIKE ?2)"
        )?;
        let search_pattern = format!("%{}%", query);
        let rows = stmt.query_map(params![session_id, search_pattern], |row| {
            Ok(FileSnapshot {
                id: row.get(0)?,
                session_id: row.get(1)?,
                file_path: row.get(2)?,
                file_name: row.get(3)?,
                extension: row.get(4)?,
                size_bytes: row.get(5)?,
                hash_sha256: row.get(6)?,
                hash_xxh64: row.get(7)?,
                modified_timestamp: row.get(8)?,
                created_timestamp: row.get(9)?,
                is_directory: row.get(10)?,
                risk_level: row.get(11)?,
                content_text: row.get(12)?,
                indexed_at: row.get(13)?,
            })
        })?;
        let mut files = Vec::new();
        for row in rows {
            files.push(row?);
        }
        Ok(files)
    }

    pub fn insert_analysis_result(&self, result: &AnalysisResult) -> SqlResult<i64> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO analysis_results (session_id, file_id, analysis_type, result_json, confidence) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![
                result.session_id,
                result.file_id,
                result.analysis_type,
                result.result_json,
                result.confidence,
            ],
        )?;
        Ok(conn.last_insert_rowid())
    }

    pub fn insert_operation_plan(&self, plan: &OperationPlan) -> SqlResult<i64> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO operation_plans (session_id, strategy, plan_json, status) VALUES (?1, ?2, ?3, ?4)",
            params![
                plan.session_id,
                plan.strategy,
                plan.plan_json,
                plan.status,
            ],
        )?;
        Ok(conn.last_insert_rowid())
    }

    pub fn insert_journal_entry(&self, entry: &JournalEntry) -> SqlResult<i64> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO journal (session_id, operation_id, operation_type, source_path, target_path, status) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                entry.session_id,
                entry.operation_id,
                entry.operation_type,
                entry.source_path,
                entry.target_path,
                entry.status,
            ],
        )?;
        Ok(conn.last_insert_rowid())
    }

    pub fn update_journal_entry(&self, id: i64, status: &str, error_message: Option<&str>) -> SqlResult<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "UPDATE journal SET status = ?1, completed_at = datetime('now'), error_message = ?2 WHERE id = ?3",
            params![status, error_message, id],
        )?;
        Ok(())
    }

    pub fn set_user_preference(&self, key: &str, value: &str, category: &str) -> SqlResult<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT OR REPLACE INTO user_preferences (key, value, category, updated_at) VALUES (?1, ?2, ?3, datetime('now'))",
            params![key, value, category],
        )?;
        Ok(())
    }

    pub fn get_user_preference(&self, key: &str) -> SqlResult<Option<String>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT value FROM user_preferences WHERE key = ?1")?;
        let mut rows = stmt.query_map(params![key], |row| row.get::<_, String>(0))?;
        match rows.next() {
            Some(row) => Ok(Some(row?)),
            None => Ok(None),
        }
    }

    pub fn insert_installed_model(&self, model: &InstalledModel) -> SqlResult<i64> {
        let conn = self.conn.lock().unwrap();
        conn.execute(
            "INSERT INTO installed_models (model_name, model_version, model_path, model_type, size_bytes, hash_sha256) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            params![
                model.model_name,
                model.model_version,
                model.model_path,
                model.model_type,
                model.size_bytes,
                model.hash_sha256,
            ],
        )?;
        Ok(conn.last_insert_rowid())
    }

    pub fn get_installed_models(&self) -> SqlResult<Vec<InstalledModel>> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare(
            "SELECT id, model_name, model_version, model_path, model_type, size_bytes, hash_sha256, installed_at, last_used_at FROM installed_models ORDER BY installed_at DESC"
        )?;
        let rows = stmt.query_map([], |row| {
            Ok(InstalledModel {
                id: row.get(0)?,
                model_name: row.get(1)?,
                model_version: row.get(2)?,
                model_path: row.get(3)?,
                model_type: row.get(4)?,
                size_bytes: row.get(5)?,
                hash_sha256: row.get(6)?,
                installed_at: row.get(7)?,
                last_used_at: row.get(8)?,
            })
        })?;
        let mut models = Vec::new();
        for row in rows {
            models.push(row?);
        }
        Ok(models)
    }

    pub fn get_file_count_by_session(&self, session_id: i64) -> SqlResult<usize> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT COUNT(*) FROM file_snapshots WHERE session_id = ?1")?;
        let count: i64 = stmt.query_row(params![session_id], |row| row.get(0))?;
        Ok(count as usize)
    }

    pub fn get_total_size_by_session(&self, session_id: i64) -> SqlResult<u64> {
        let conn = self.conn.lock().unwrap();
        let mut stmt = conn.prepare("SELECT COALESCE(SUM(size_bytes), 0) FROM file_snapshots WHERE session_id = ?1")?;
        let total: i64 = stmt.query_row(params![session_id], |row| row.get(0))?;
        Ok(total as u64)
    }

    pub fn delete_session(&self, id: i64) -> SqlResult<()> {
        let conn = self.conn.lock().unwrap();
        conn.execute("DELETE FROM sessions WHERE id = ?1", params![id])?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::TempDir;

    #[test]
    fn test_database_creation() {
        let temp_dir = TempDir::new().unwrap();
        let db_path = temp_dir.path().join("test.db");
        let _db = DatabaseManager::new(&db_path).unwrap();
        assert!(db_path.exists());
    }

    #[test]
    fn test_in_memory_database() {
        let db = DatabaseManager::new_in_memory().unwrap();
        let session_id = db.create_session("Test Session", "/test/path").unwrap();
        assert!(session_id > 0);
    }

    #[test]
    fn test_session_crud() {
        let db = DatabaseManager::new_in_memory().unwrap();
        
        let session_id = db.create_session("My Project", "C:\\Users\\test\\project").unwrap();
        let session = db.get_session(session_id).unwrap().unwrap();
        assert_eq!(session.name, "My Project");
        assert_eq!(session.root_path, "C:\\Users\\test\\project");
        assert_eq!(session.status, "active");

        let sessions = db.list_sessions().unwrap();
        assert_eq!(sessions.len(), 1);
    }

    #[test]
    fn test_file_snapshot_operations() {
        let db = DatabaseManager::new_in_memory().unwrap();
        let session_id = db.create_session("Test", "/test").unwrap();

        let snapshot = FileSnapshot {
            id: 0,
            session_id,
            file_path: "/test/document.pdf".to_string(),
            file_name: "document.pdf".to_string(),
            extension: "pdf".to_string(),
            size_bytes: 1024,
            hash_sha256: Some("abc123".to_string()),
            hash_xxh64: Some(12345),
            modified_timestamp: 1000000,
            created_timestamp: 999999,
            is_directory: false,
            risk_level: "safe".to_string(),
            content_text: Some("PDF document content".to_string()),
            indexed_at: "2024-01-01 00:00:00".to_string(),
        };

        let file_id = db.insert_file_snapshot(&snapshot).unwrap();
        assert!(file_id > 0);

        let search_results = db.search_files(session_id, "document").unwrap();
        assert_eq!(search_results.len(), 1);

        let count = db.get_file_count_by_session(session_id).unwrap();
        assert_eq!(count, 1);

        let total_size = db.get_total_size_by_session(session_id).unwrap();
        assert_eq!(total_size, 1024);
    }

    #[test]
    fn test_user_preferences() {
        let db = DatabaseManager::new_in_memory().unwrap();
        
        db.set_user_preference("scan_depth", "10", "general").unwrap();
        db.set_user_preference("model_lane", "balanced", "models").unwrap();

        let depth = db.get_user_preference("scan_depth").unwrap().unwrap();
        assert_eq!(depth, "10");

        let lane = db.get_user_preference("model_lane").unwrap().unwrap();
        assert_eq!(lane, "balanced");

        db.set_user_preference("scan_depth", "20", "general").unwrap();
        let updated = db.get_user_preference("scan_depth").unwrap().unwrap();
        assert_eq!(updated, "20");
    }

    #[test]
    fn test_journal_operations() {
        let db = DatabaseManager::new_in_memory().unwrap();
        let session_id = db.create_session("Test", "/test").unwrap();

        let entry = JournalEntry {
            id: 0,
            session_id,
            operation_id: "op-001".to_string(),
            operation_type: "move".to_string(),
            source_path: "/test/file.txt".to_string(),
            target_path: Some("/test/archive/file.txt".to_string()),
            status: "pending".to_string(),
            created_at: "2024-01-01 00:00:00".to_string(),
            completed_at: None,
            error_message: None,
        };

        let entry_id = db.insert_journal_entry(&entry).unwrap();
        assert!(entry_id > 0);

        db.update_journal_entry(entry_id, "completed", None).unwrap();
    }

    #[test]
    fn test_installed_models() {
        let db = DatabaseManager::new_in_memory().unwrap();

        let model = InstalledModel {
            id: 0,
            model_name: "Gemma-4-E2B".to_string(),
            model_version: "1.0.0".to_string(),
            model_path: "/models/gemma-4-e2b.gguf".to_string(),
            model_type: "llm".to_string(),
            size_bytes: 2_000_000_000,
            hash_sha256: Some("def456".to_string()),
            installed_at: "2024-01-01 00:00:00".to_string(),
            last_used_at: None,
        };

        let model_id = db.insert_installed_model(&model).unwrap();
        assert!(model_id > 0);

        let models = db.get_installed_models().unwrap();
        assert_eq!(models.len(), 1);
        assert_eq!(models[0].model_name, "Gemma-4-E2B");
    }

    #[test]
    fn test_session_deletion_cascade() {
        let db = DatabaseManager::new_in_memory().unwrap();
        let session_id = db.create_session("Test", "/test").unwrap();

        let snapshot = FileSnapshot {
            id: 0,
            session_id,
            file_path: "/test/file.txt".to_string(),
            file_name: "file.txt".to_string(),
            extension: "txt".to_string(),
            size_bytes: 100,
            hash_sha256: None,
            hash_xxh64: None,
            modified_timestamp: 0,
            created_timestamp: 0,
            is_directory: false,
            risk_level: "safe".to_string(),
            content_text: None,
            indexed_at: "2024-01-01 00:00:00".to_string(),
        };

        db.insert_file_snapshot(&snapshot).unwrap();
        assert_eq!(db.get_file_count_by_session(session_id).unwrap(), 1);

        db.delete_session(session_id).unwrap();
        assert_eq!(db.get_file_count_by_session(session_id).unwrap(), 0);
    }
}
