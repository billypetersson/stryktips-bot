-- Deactivate week 43
UPDATE coupons SET is_active = false WHERE week_number = 43 AND year = 2025;

-- Create week 44 coupon if it doesn't exist
INSERT INTO coupons (week_number, year, draw_date, is_active, jackpot_amount, created_at, updated_at)
VALUES (44, 2025, NOW() + INTERVAL '7 days', true, 10000000, NOW(), NOW())
ON CONFLICT (week_number) DO UPDATE SET is_active = true;

-- Get the coupon ID for week 44
DO $$
DECLARE
    v_coupon_id INTEGER;
    v_match_id INTEGER;
BEGIN
    -- Get coupon ID
    SELECT id INTO v_coupon_id FROM coupons WHERE week_number = 44 AND year = 2025;

    -- Delete existing match 1 if it exists
    DELETE FROM matches WHERE coupon_id = v_coupon_id AND match_number = 1;

    -- Insert Liverpool - Aston Villa
    INSERT INTO matches (
        coupon_id,
        match_number,
        home_team,
        away_team,
        kickoff_time,
        home_percentage,
        draw_percentage,
        away_percentage,
        created_at
    ) VALUES (
        v_coupon_id,
        1,
        'Liverpool',
        'Aston Villa',
        NOW() + INTERVAL '7 days',
        51.0,
        22.0,
        27.0,
        NOW()
    ) RETURNING id INTO v_match_id;

    -- Add odds
    INSERT INTO odds (
        match_id,
        bookmaker,
        home_odds,
        draw_odds,
        away_odds,
        home_probability,
        draw_probability,
        away_probability,
        fetched_at
    ) VALUES (
        v_match_id,
        'test',
        1.57,
        4.75,
        5.60,
        1.0/1.57 / (1.0/1.57 + 1.0/4.75 + 1.0/5.60),
        1.0/4.75 / (1.0/1.57 + 1.0/4.75 + 1.0/5.60),
        1.0/5.60 / (1.0/1.57 + 1.0/4.75 + 1.0/5.60),
        NOW()
    );

    RAISE NOTICE 'Liverpool - Aston Villa added to week 44!';
END $$;
