-- Preserve all historical FKs and snapshots; prebuilt exams cannot be started.
UPDATE assessment SET status = 'closed' WHERE status = 'published';
