BEGIN;

SELECT _v.register_patch('0004-add-starboard-guild-config', ARRAY['0003-fix-message-star-trigger'], NULL);

CREATE OR REPLACE FUNCTION public.starboard_guild_config_trigger_function()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    INSERT INTO starboard_guild_config (guild_id)
    VALUES (new.guild_id)
    ON CONFLICT (guild_id) DO NOTHING;
    RETURN NULL;
END
$BODY$;

CREATE TABLE IF NOT EXISTS public.starboard_guild_config
(
    guild_id bigint NOT NULL,
    starboard_channel_id bigint,
    CONSTRAINT starboard_guild_config_pkey PRIMARY KEY (guild_id),
    CONSTRAINT starboard_guild_config_guild_id_fkey FOREIGN KEY (guild_id)
        REFERENCES public.guild (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT starboard_guild_config_starboard_channel_id_fkey FOREIGN KEY (starboard_channel_id)
        REFERENCES public.channel (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

CREATE OR REPLACE TRIGGER starboard_guild_config_trigger
    AFTER INSERT
    ON public.guild
    FOR EACH ROW
    EXECUTE FUNCTION public.starboard_guild_config_trigger_function();

END;
