-- DBCAS development seed (runs after schema.sql via docker-entrypoint-initdb.d)
-- Dev baseline only — never run against a production database.

-- Reference roles required by UC01/UC04 (self-registration needs 'Learner').
INSERT INTO role (role_name, description) VALUES
  ('Learner', 'Takes adaptive assessments and views competency results'),
  ('Administrator', 'Curates CLOs, questions, rubrics; reviews analytics')
ON CONFLICT (role_name) DO NOTHING;

-- Bootstrap administrator for local development.
-- Email: admin@dbcas.local  Password: Admin123!  (change/remove outside dev)
INSERT INTO account (email, password_hash, status) VALUES
  ('admin@dbcas.local',
   '$2b$12$9vy.Djy6R1YgswsHaQD7h.XqZ6JlQ/DgSi7LFicQDcyGufQRjrUEa',
   'active')
ON CONFLICT (email) DO NOTHING;

INSERT INTO user_profile (account_id, full_name)
SELECT account_id, 'Dev Administrator' FROM account WHERE email = 'admin@dbcas.local'
ON CONFLICT (account_id) DO NOTHING;

INSERT INTO account_role (account_id, role_id)
SELECT a.account_id, r.role_id
FROM account a, role r
WHERE a.email = 'admin@dbcas.local' AND r.role_name = 'Administrator'
ON CONFLICT DO NOTHING;
