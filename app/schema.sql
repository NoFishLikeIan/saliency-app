DROP TABLE IF EXISTS saliency;

CREATE TABLE saliency (
    report TEXT NOT NULL,
    company TEXT NOT NULL,
    word TEXT NOT NULL,
    score REAL NOT NULL
);