BEGIN;

SELECT _v.register_patch('0003-fix-message-star-trigger', ARRAY['0002-unique-message-id'], NULL);

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
		INSERT INTO message_star_total AS mst (message_id, total)
		VALUES (new.message_id, 1)
		ON CONFLICT (message_id) DO UPDATE SET total = mst.total + 1;
	END IF;
	RETURN NULL;
END
$BODY$;

COMMIT;
