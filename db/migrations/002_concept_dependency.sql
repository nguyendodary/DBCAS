-- Additive prerequisite graph upgrade for existing volumes; safe to repeat.
CREATE TABLE IF NOT EXISTS concept_dependency (
  concept_id INT NOT NULL REFERENCES concept(concept_id),
  prerequisite_concept_id INT NOT NULL REFERENCES concept(concept_id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (concept_id, prerequisite_concept_id),
  CHECK (concept_id <> prerequisite_concept_id)
);
CREATE INDEX IF NOT EXISTS concept_dependency_prerequisite_idx
  ON concept_dependency(prerequisite_concept_id);
