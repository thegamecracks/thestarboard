BEGIN;

SELECT _v.register_patch('0006-fix-starboard-guild-config-trigger', ARRAY['0005-add-comments'], NULL);

CREATE OR REPLACE FUNCTION public.starboard_guild_config_trigger_function()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    VOLATILE
    COST 100
AS $BODY$
BEGIN
    INSERT INTO starboard_guild_config (guild_id)
    VALUES (new.id)
    ON CONFLICT (guild_id) DO NOTHING;
    RETURN NULL;
END
$BODY$;

COMMIT;
