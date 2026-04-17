DO $$
BEGIN
    IF to_regclass('searches') IS NULL THEN
        RETURN;
    END IF;

    ALTER TABLE searches
        ALTER COLUMN radius DROP NOT NULL;

    ALTER TABLE searches
        ADD COLUMN IF NOT EXISTS search_type VARCHAR(10);

    UPDATE searches
    SET search_type = 'zone'
    WHERE search_type IS NULL;

    ALTER TABLE searches
        ALTER COLUMN search_type SET DEFAULT 'zone';

    ALTER TABLE searches
        ALTER COLUMN search_type SET NOT NULL;

    ALTER TABLE searches
        DROP CONSTRAINT IF EXISTS ck_search_type_valid;

    ALTER TABLE searches
        ADD CONSTRAINT ck_search_type_valid
        CHECK (search_type IN ('zone', 'route'));
END
$$;
