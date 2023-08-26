BEGIN;

SELECT _v.register_patch('0002-unique-message-id', ARRAY['0001-base'], NULL);

-- Drops PK, FK
ALTER TABLE IF EXISTS public.starboard_message DROP COLUMN IF EXISTS channel_id;
-- Drops FK
ALTER TABLE IF EXISTS public.starboard_message DROP COLUMN IF EXISTS star_channel_id;
-- Drops PK, FK
ALTER TABLE IF EXISTS public.message_star_total DROP COLUMN IF EXISTS channel_id;

CREATE OR REPLACE FUNCTION public.message_star_total_trigger_function()
    RETURNS trigger
    LANGUAGE 'plpgsql'
    VOLATILE
    COST 100
AS $BODY$
BEGIN
    IF TG_OP IN ('UPDATE', 'DELETE') THEN
        UPDATE message_star_total SET total = total - 1
        WHERE message_id = old.message_id;
        -- NOTE: message_star_total is not automatically deleted here
    END IF;
    IF TG_OP IN ('INSERT', 'UPDATE') THEN
        INSERT INTO message_star_total (message_id, total)
        VALUES (new.message_id, 1)
        ON CONFLICT DO UPDATE SET total = total + 1;
    END IF;
    RETURN NULL;
END
$BODY$;

CREATE OR REPLACE TRIGGER message_star_total_trigger
    AFTER INSERT OR DELETE OR UPDATE OF message_id
    ON public.message_star
    FOR EACH ROW
    EXECUTE FUNCTION public.message_star_total_trigger_function();

-- Drops UNIQUE, FK
ALTER TABLE IF EXISTS public.message_star DROP COLUMN IF EXISTS channel_id;
-- Drops PK
ALTER TABLE IF EXISTS public.message DROP CONSTRAINT IF EXISTS message_pkey;

-- Restore constraints
ALTER TABLE IF EXISTS public.message
    ADD PRIMARY KEY (id);

ALTER TABLE IF EXISTS public.message_star
    ADD UNIQUE NULLS NOT DISTINCT (message_id, user_id, emoji);
ALTER TABLE IF EXISTS public.message_star
    ADD FOREIGN KEY (message_id)
    REFERENCES public.message (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE CASCADE;

ALTER TABLE IF EXISTS public.message_star_total
    ADD PRIMARY KEY (message_id);
ALTER TABLE IF EXISTS public.message_star_total
    ADD FOREIGN KEY (message_id)
    REFERENCES public.message (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE CASCADE;

ALTER TABLE IF EXISTS public.starboard_message
    ADD PRIMARY KEY (message_id);
ALTER TABLE IF EXISTS public.starboard_message
    ADD FOREIGN KEY (message_id)
    REFERENCES public.message (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE CASCADE;
ALTER TABLE IF EXISTS public.starboard_message
    ADD FOREIGN KEY (star_message_id)
    REFERENCES public.message (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE NO ACTION
    NOT VALID;

COMMIT;
