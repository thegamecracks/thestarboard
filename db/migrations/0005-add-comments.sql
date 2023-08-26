BEGIN;

SELECT _v.register_patch('0005-add-comments', ARRAY['0004-add-starboard-guild-config'], NULL);

COMMENT ON TRIGGER message_star_total_trigger ON public.message_star
    IS 'Maintains a corresponding message_star_total row as stars are inserted/updated/deleted.';

COMMENT ON TABLE public.starboard_guild_config
  IS 'Stores per-guild starboard configuration.';

COMMENT ON TRIGGER starboard_guild_config_trigger ON public.guild
    IS 'Inserts a corresponding starboard config row for new guilds.';

COMMIT;
