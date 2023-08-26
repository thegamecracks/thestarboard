BEGIN;

SELECT _v.register_patch('0007-add-starboard-threshold', ARRAY['0006-fix-starboard-guild-config-trigger'], NULL);

ALTER TABLE IF EXISTS public.starboard_guild_config
    ADD COLUMN starboard_threshold smallint NOT NULL DEFAULT 3;

COMMIT;
