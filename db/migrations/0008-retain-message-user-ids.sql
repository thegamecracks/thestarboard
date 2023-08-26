BEGIN;

SELECT _v.register_patch('0008-retain-message-user-ids', ARRAY['0007-add-starboard-threshold'], NULL);

ALTER TABLE IF EXISTS public.message
    ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE IF EXISTS public.message DROP CONSTRAINT IF EXISTS message_user_id_fkey;
ALTER TABLE IF EXISTS public.message
    ADD CONSTRAINT message_user_id_fkey FOREIGN KEY (user_id)
    REFERENCES public."user" (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE NO ACTION
    NOT VALID;

ALTER TABLE IF EXISTS public.message_star
    ALTER COLUMN user_id SET NOT NULL;

ALTER TABLE IF EXISTS public.message_star DROP CONSTRAINT IF EXISTS message_star_user_id_fkey;
ALTER TABLE IF EXISTS public.message_star
    ADD CONSTRAINT message_star_user_id_fkey FOREIGN KEY (user_id)
    REFERENCES public."user" (id) MATCH SIMPLE
    ON UPDATE CASCADE
    ON DELETE NO ACTION
    NOT VALID;

COMMIT;
