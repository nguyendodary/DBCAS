-- Optional curated pool; an empty pool keeps existing concept-based selection.
CREATE TABLE IF NOT EXISTS assessment_question (
  assessment_id INT NOT NULL REFERENCES assessment(assessment_id) ON DELETE CASCADE,
  question_id INT NOT NULL REFERENCES question(question_id),
  PRIMARY KEY (assessment_id, question_id)
);
CREATE INDEX IF NOT EXISTS assessment_question_question_idx ON assessment_question(question_id);
