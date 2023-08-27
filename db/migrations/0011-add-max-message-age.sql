BEGIN;

SELECT _v.register_patch('0011-add-max-message-age', ARRAY['0010-rename-star-threshold'], NULL);

ALTER TABLE IF EXISTS public.starboard_guild_config
    ADD COLUMN max_message_age integer NOT NULL DEFAULT 86400 * 7;

COMMIT;
