-- Reference roles are required independently of development/demo accounts.
INSERT INTO role (role_name, description) VALUES
  ('Learner', 'Takes adaptive assessments and views competency results'),
  ('Administrator', 'Curates curriculum, questions and assessments')
ON CONFLICT (role_name) DO NOTHING;
