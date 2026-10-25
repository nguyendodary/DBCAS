-- Additive: keep historical single selections intact.
ALTER TABLE attempt ADD COLUMN IF NOT EXISTS selected_option_ids JSONB;
UPDATE attempt SET selected_option_ids = jsonb_build_array(selected_option_id)
WHERE selected_option_ids IS NULL AND selected_option_id IS NOT NULL;
