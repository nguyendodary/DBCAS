-- DBCAS schema (PostgreSQL 17)

CREATE TABLE account (
  account_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE role (
  role_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  role_name VARCHAR(50) NOT NULL UNIQUE,
  description TEXT
);

CREATE TABLE account_role (
  account_id INT NOT NULL,
  role_id INT NOT NULL,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (account_id, role_id)
);

CREATE TABLE user_profile (
  user_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  account_id INT NOT NULL UNIQUE,
  full_name VARCHAR(100) NOT NULL,
  student_code VARCHAR(20),
  phone_number VARCHAR(20),
  date_of_birth DATE
);

CREATE TABLE course_learning_outcome (
  clo_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  clo_code VARCHAR(20) NOT NULL UNIQUE,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'active',
  created_by INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE concept (
  concept_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  concept_code VARCHAR(30) NOT NULL UNIQUE,
  concept_name VARCHAR(100) NOT NULL,
  subject_area VARCHAR(100) NOT NULL,
  description TEXT,
  difficulty_level SMALLINT NOT NULL DEFAULT 1,
  CHECK (difficulty_level BETWEEN 1 AND 5)
);

CREATE TABLE clo_concept (
  clo_id INT NOT NULL,
  concept_id INT NOT NULL,
  mapping_source VARCHAR(10) NOT NULL DEFAULT 'admin',
  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (clo_id, concept_id)
);

-- Prerequisite skill graph: concept_id depends on prerequisite_concept_id.
-- Directed edge prerequisite -> concept; the PK also blocks duplicate edges
-- and the CHECK blocks self-dependency. Transitive-cycle freedom is enforced
-- by the service layer on every write (a CHECK cannot see transitive edges).
CREATE TABLE concept_dependency (
  concept_id INT NOT NULL,
  prerequisite_concept_id INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (concept_id, prerequisite_concept_id),
  CHECK (concept_id <> prerequisite_concept_id)
);

CREATE TABLE question (
  question_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question_type VARCHAR(10) NOT NULL,
  prompt TEXT NOT NULL,
  reference_answer TEXT,
  difficulty_level SMALLINT NOT NULL DEFAULT 1,
  points NUMERIC(5,2) NOT NULL DEFAULT 1.0,
  source VARCHAR(15) NOT NULL DEFAULT 'bank',
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  created_by INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (question_type IN ('mcq', 'sql', 'essay')),
  CHECK (difficulty_level BETWEEN 1 AND 5)
);

CREATE TABLE question_concept (
  question_id INT NOT NULL,
  concept_id INT NOT NULL,
  tag_source VARCHAR(10) NOT NULL DEFAULT 'admin',
  is_required BOOLEAN NOT NULL DEFAULT FALSE,
  confirmed BOOLEAN NOT NULL DEFAULT FALSE,
  PRIMARY KEY (question_id, concept_id)
);

CREATE TABLE mcq_option (
  option_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question_id INT NOT NULL,
  option_label VARCHAR(5) NOT NULL,
  option_text TEXT NOT NULL,
  is_correct BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE sql_test_dataset (
  dataset_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question_id INT NOT NULL,
  dataset_name VARCHAR(100) NOT NULL,
  setup_sql TEXT NOT NULL,
  expected_result JSONB NOT NULL,
  is_edge_case BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE rubric (
  rubric_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  question_id INT NOT NULL,
  level_name VARCHAR(30) NOT NULL,
  min_score NUMERIC(5,2) NOT NULL,
  max_score NUMERIC(5,2) NOT NULL,
  criteria TEXT NOT NULL,
  CHECK (min_score <= max_score)
);

CREATE TABLE assessment (
  assessment_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  max_questions SMALLINT NOT NULL DEFAULT 13,
  duration_min SMALLINT NOT NULL DEFAULT 60,
  target_mcq SMALLINT NOT NULL DEFAULT 10,
  target_sql SMALLINT NOT NULL DEFAULT 2,
  target_essay SMALLINT NOT NULL DEFAULT 1,
  status VARCHAR(20) NOT NULL DEFAULT 'draft',
  created_by INT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CHECK (max_questions BETWEEN 1 AND 13),
  CHECK (target_mcq + target_sql + target_essay <= max_questions)
);

CREATE TABLE assessment_concept (
  assessment_id INT NOT NULL,
  concept_id INT NOT NULL,
  min_difficulty SMALLINT NOT NULL DEFAULT 1,
  max_difficulty SMALLINT NOT NULL DEFAULT 5,
  target_pct NUMERIC(5,2) NOT NULL,
  PRIMARY KEY (assessment_id, concept_id),
  CHECK (min_difficulty BETWEEN 1 AND 5),
  CHECK (max_difficulty BETWEEN min_difficulty AND 5),
  CHECK (target_pct BETWEEN 0 AND 100)
);

CREATE TABLE assessment_session (
  session_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  assessment_id INT NOT NULL,
  learner_id INT NOT NULL,
  status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  submitted_at TIMESTAMPTZ,
  CHECK (status IN ('in_progress', 'completed', 'timed_out'))
);

CREATE TABLE attempt (
  attempt_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  question_id INT NOT NULL,
  seq_no SMALLINT NOT NULL,
  selected_option_id INT,
  sql_answer TEXT,
  essay_answer TEXT,
  score NUMERIC(5,2),
  grading_detail JSONB,
  served_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  submitted_at TIMESTAMPTZ,
  UNIQUE (session_id, seq_no)
);

CREATE TABLE selection_log (
  log_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  seq_no SMALLINT NOT NULL,
  question_id INT NOT NULL,
  is_fallback BOOLEAN NOT NULL DEFAULT FALSE,
  decision_detail JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, seq_no)
);

CREATE TABLE concept_competency (
  competency_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  concept_id INT NOT NULL,
  points_earned NUMERIC(6,2) NOT NULL DEFAULT 0,
  points_possible NUMERIC(6,2) NOT NULL DEFAULT 0,
  competency_pct NUMERIC(5,2) NOT NULL DEFAULT 0,
  below_target BOOLEAN NOT NULL DEFAULT FALSE,
  computed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, concept_id)
);

CREATE TABLE competency_gap (
  gap_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  session_id INT NOT NULL,
  concept_id INT NOT NULL,
  llm_explanation TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'open',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (session_id, concept_id)
);

CREATE TABLE llm_cache (
  cache_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  request_hash VARCHAR(64) NOT NULL UNIQUE,
  task_type VARCHAR(30) NOT NULL,
  model VARCHAR(50) NOT NULL,
  response JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE question_candidate (
  candidate_id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  concept_id INT NOT NULL,
  question_type VARCHAR(10) NOT NULL,
  payload JSONB NOT NULL,
  validation_status VARCHAR(20) NOT NULL DEFAULT 'pending',
  validation_detail JSONB,
  promoted_question_id INT UNIQUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE account_role ADD FOREIGN KEY (account_id) REFERENCES account (account_id);
ALTER TABLE account_role ADD FOREIGN KEY (role_id) REFERENCES role (role_id);
ALTER TABLE user_profile ADD FOREIGN KEY (account_id) REFERENCES account (account_id);
ALTER TABLE course_learning_outcome ADD FOREIGN KEY (created_by) REFERENCES account (account_id);
ALTER TABLE clo_concept ADD FOREIGN KEY (clo_id) REFERENCES course_learning_outcome (clo_id);
ALTER TABLE clo_concept ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE concept_dependency ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE concept_dependency ADD FOREIGN KEY (prerequisite_concept_id) REFERENCES concept (concept_id);
ALTER TABLE question ADD FOREIGN KEY (created_by) REFERENCES account (account_id);
ALTER TABLE question_concept ADD FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE question_concept ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE mcq_option ADD FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE sql_test_dataset ADD FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE rubric ADD FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE assessment ADD FOREIGN KEY (created_by) REFERENCES account (account_id);
ALTER TABLE assessment_concept ADD FOREIGN KEY (assessment_id) REFERENCES assessment (assessment_id);
ALTER TABLE assessment_concept ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE assessment_session ADD FOREIGN KEY (assessment_id) REFERENCES assessment (assessment_id);
ALTER TABLE assessment_session ADD FOREIGN KEY (learner_id) REFERENCES account (account_id);
ALTER TABLE attempt ADD FOREIGN KEY (session_id) REFERENCES assessment_session (session_id);
ALTER TABLE attempt ADD FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE attempt ADD FOREIGN KEY (selected_option_id) REFERENCES mcq_option (option_id);
ALTER TABLE selection_log ADD FOREIGN KEY (session_id) REFERENCES assessment_session (session_id);
ALTER TABLE selection_log ADD FOREIGN KEY (question_id) REFERENCES question (question_id);
ALTER TABLE concept_competency ADD FOREIGN KEY (session_id) REFERENCES assessment_session (session_id);
ALTER TABLE concept_competency ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE competency_gap ADD FOREIGN KEY (session_id) REFERENCES assessment_session (session_id);
ALTER TABLE competency_gap ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE question_candidate ADD FOREIGN KEY (concept_id) REFERENCES concept (concept_id);
ALTER TABLE question_candidate ADD FOREIGN KEY (promoted_question_id) REFERENCES question (question_id);
