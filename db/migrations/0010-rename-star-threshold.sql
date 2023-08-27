BEGIN;

SELECT _v.register_patch('0010-rename-star-threshold', ARRAY['0009-one-star-per-message-user'], NULL);

ALTER TABLE IF EXISTS public.starboard_guild_config
    RENAME starboard_threshold TO star_threshold;

COMMIT;
