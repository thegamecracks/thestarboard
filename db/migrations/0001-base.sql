BEGIN;

SELECT _v.register_patch('0001-base', NULL, NULL);

CREATE TABLE IF NOT EXISTS public.guild
(
    id bigint NOT NULL,
    CONSTRAINT guild_pkey PRIMARY KEY (id)
);

COMMENT ON TABLE public.guild
    IS 'Represents a Discord guild.';

CREATE TABLE IF NOT EXISTS public.channel
(
    id bigint NOT NULL,
    guild_id bigint,
    CONSTRAINT channel_pkey PRIMARY KEY (id),
    CONSTRAINT channel_id_guild_id_key UNIQUE (id, guild_id),
    CONSTRAINT channel_guild_id_fkey FOREIGN KEY (guild_id)
        REFERENCES public.guild (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

COMMENT ON TABLE public.channel
    IS 'Represents a Discord channel.';

CREATE TABLE IF NOT EXISTS public."user"
(
    id bigint NOT NULL,
    CONSTRAINT user_pkey PRIMARY KEY (id)
);

COMMENT ON TABLE public."user"
    IS 'Represents a Discord user.';

CREATE TABLE IF NOT EXISTS public.message
(
    id bigint NOT NULL,
    channel_id bigint NOT NULL,
    user_id bigint,
    CONSTRAINT message_pkey PRIMARY KEY (id, channel_id),
    CONSTRAINT message_channel_id_fkey FOREIGN KEY (channel_id)
        REFERENCES public.channel (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT message_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public."user" (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

COMMENT ON TABLE public.message
    IS 'Represents a Discord message.';

CREATE TABLE IF NOT EXISTS public.message_star
(
    message_id bigint NOT NULL,
    channel_id bigint NOT NULL,
    user_id bigint,
    emoji text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT message_star_message_id_channel_id_user_id_emoji_key UNIQUE NULLS NOT DISTINCT (message_id, channel_id, user_id, emoji),
    CONSTRAINT message_star_message_id_channel_id_fkey FOREIGN KEY (message_id, channel_id)
        REFERENCES public.message (id, channel_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT message_star_user_id_fkey FOREIGN KEY (user_id)
        REFERENCES public."user" (id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE SET NULL
);

COMMENT ON TABLE public.message_star
    IS 'Stores star reactions for messages.';

CREATE TABLE IF NOT EXISTS public.message_star_total
(
    message_id bigint NOT NULL,
    channel_id bigint NOT NULL,
    total smallint NOT NULL DEFAULT 0,
    CONSTRAINT message_star_total_pkey PRIMARY KEY (message_id, channel_id),
    CONSTRAINT message_star_total_message_id_channel_id_fkey FOREIGN KEY (message_id, channel_id)
        REFERENCES public.message (id, channel_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE
);

COMMENT ON TABLE public.message_star_total
    IS 'Stores the total number of stars that a message has received.';

CREATE TABLE IF NOT EXISTS public.starboard_message
(
    message_id bigint NOT NULL,
    channel_id bigint NOT NULL,
    star_message_id bigint NOT NULL,
    star_channel_id bigint NOT NULL,
    CONSTRAINT starboard_message_pkey PRIMARY KEY (channel_id, message_id),
    CONSTRAINT starboard_message_message_id_channel_id_fkey FOREIGN KEY (message_id, channel_id)
        REFERENCES public.message (id, channel_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE CASCADE,
    CONSTRAINT starboard_message_star_message_id_star_channel_id_fkey FOREIGN KEY (star_message_id, star_channel_id)
        REFERENCES public.message (id, channel_id) MATCH SIMPLE
        ON UPDATE CASCADE
        ON DELETE NO ACTION
        NOT VALID
);

COMMENT ON TABLE public.starboard_message
    IS 'Stores a starboard message.';

CREATE OR REPLACE FUNCTION public.message_star_total_trigger_function()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    COST 100
    VOLATILE NOT LEAKPROOF
AS $BODY$
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        UPDATE message_star_total SET total = total - 1
        WHERE message_id = old.message_id AND channel_id = old.channel_id;
        -- NOTE: message_star_total is not automatically deleted here
    END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        INSERT INTO message_star_total (message_id, channel_id, total)
        VALUES (new.message_id, new.channel_id, 1)
        ON CONFLICT DO UPDATE SET total = total + 1;
    END IF;
    RETURN NULL;
END
$BODY$;

CREATE OR REPLACE TRIGGER message_star_total_trigger
    AFTER INSERT OR DELETE OR UPDATE OF message_id, channel_id
    ON public.message_star
    FOR EACH ROW
    EXECUTE FUNCTION public.message_star_total_trigger_function();

COMMIT;
