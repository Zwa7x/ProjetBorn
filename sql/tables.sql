PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS regions (
  acronym TEXT PRIMARY KEY,
  long_name TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS places (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  region_acronym TEXT NOT NULL,
  address TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(region_acronym) REFERENCES regions(acronym) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS charger_types (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  code TEXT UNIQUE NOT NULL,
  label TEXT NOT NULL,
  specs TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE VIEW IF NOT EXISTS region_summary AS
SELECT r.acronym, r.long_name, COUNT(p.id) AS place_count
FROM regions r
LEFT JOIN places p ON p.region_acronym = r.acronym
GROUP BY r.acronym, r.long_name;
