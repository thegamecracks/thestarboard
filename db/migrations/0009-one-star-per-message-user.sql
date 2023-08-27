BEGIN;

SELECT _v.register_patch('0009-one-star-per-message-user', ARRAY['0008-retain-message-user-ids'], NULL);

-- Delete duplicate rows before creating primary key
WITH first_ms AS (
	SELECT message_id, user_id, emoji FROM (
		SELECT
			message_id, user_id, emoji,
			row_number() OVER (
				PARTITION BY message_id, user_id
			) AS i
		FROM message_star
	) sub_query
	WHERE i = 1
)
DELETE FROM message_star ms WHERE ms = (message_id, user_id, emoji);

ALTER TABLE IF EXISTS public.message_star
    ADD CONSTRAINT message_star_pkey PRIMARY KEY (message_id, user_id);

ALTER TABLE IF EXISTS public.message_star DROP CONSTRAINT IF EXISTS message_star_message_id_user_id_emoji_key;

COMMIT;
