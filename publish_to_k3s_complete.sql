-- Complete script to publish Liverpool - Aston Villa to k3s with analysis
-- This includes: coupon, match, odds, analysis, and suggested rows

-- Step 1: Deactivate old coupons
UPDATE coupons SET is_active = false WHERE is_active = true;

-- Step 2: Create or update week 44 coupon
INSERT INTO coupons (week_number, year, draw_date, is_active, jackpot_amount, created_at, updated_at)
VALUES (44, 2025, NOW() + INTERVAL '7 days', true, 10000000, NOW(), NOW())
ON CONFLICT (week_number) DO UPDATE
SET is_active = true, updated_at = NOW();

-- Step 3: Add Liverpool - Aston Villa match with analysis and system suggestions
DO $$
DECLARE
    v_coupon_id INTEGER;
    v_match_id INTEGER;
    v_odds_id INTEGER;
    v_analysis_id INTEGER;
BEGIN
    -- Get coupon ID
    SELECT id INTO v_coupon_id FROM coupons WHERE week_number = 44 AND year = 2025;

    IF v_coupon_id IS NULL THEN
        RAISE EXCEPTION 'Coupon 44/2025 not found!';
    END IF;

    -- Delete existing match 1 and all related data
    DELETE FROM matches WHERE coupon_id = v_coupon_id AND match_number = 1;

    -- Insert match
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

    RAISE NOTICE 'Created match with ID: %', v_match_id;

    -- Insert odds
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
    ) RETURNING id INTO v_odds_id;

    RAISE NOTICE 'Created odds with ID: %', v_odds_id;

    -- Insert analysis
    INSERT INTO analyses (
        match_id,
        avg_home_odds,
        avg_draw_odds,
        avg_away_odds,
        true_home_prob,
        true_draw_prob,
        true_away_prob,
        home_value,
        draw_value,
        away_value,
        recommended_signs,
        expert_summary,
        calculated_at
    ) VALUES (
        v_match_id,
        1.57,
        4.75,
        5.60,
        0.6207773719646671,
        0.2051832576809531,
        0.17403937035437989,
        1.217210533264053,
        0.9326511712770595,
        0.6445902605717773,
        '1',
        'Stark värdefavorit. Liverpool har 62% sannolikhet att vinna enligt beräkningarna, vilket ger ett värde på 1.22 på ettan. Svenska folket understreckar med bara 51% på 1.',
        NOW()
    ) RETURNING id INTO v_analysis_id;

    RAISE NOTICE 'Created analysis with ID: %', v_analysis_id;

    -- Delete old suggested rows for this coupon
    DELETE FROM suggested_rows WHERE coupon_id = v_coupon_id;

    -- Insert suggested rows
    -- Row 1: Primary row (all "1")
    INSERT INTO suggested_rows (
        coupon_id,
        row_data,
        half_cover_count,
        expected_value,
        cost_factor,
        reasoning,
        generated_at
    ) VALUES (
        v_coupon_id,
        '{"1": "1", "2": "1", "3": "1", "4": "1", "5": "1", "6": "1", "7": "1", "8": "1", "9": "1", "10": "1", "11": "1", "12": "1", "13": "1"}',
        0,
        0.09363157948185023,
        1,
        'Primär rad med högsta värdet per match. Inga helgarderingar.',
        NOW()
    );

    -- Row 2: With half cover on match 1
    INSERT INTO suggested_rows (
        coupon_id,
        row_data,
        half_cover_count,
        expected_value,
        cost_factor,
        reasoning,
        generated_at
    ) VALUES (
        v_coupon_id,
        '{"1": "1X", "2": "1", "3": "1", "4": "1", "5": "1", "6": "1", "7": "1", "8": "1", "9": "1", "10": "1", "11": "1", "12": "1", "13": "1"}',
        1,
        0.16537397727239328,
        2,
        'Alternativ rad med 1 helgardering på match 1 (Liverpool). Högre förväntat värde trots dubbel kostnad. Rekommenderad!',
        NOW()
    );

    RAISE NOTICE 'Created 2 suggested rows';
    RAISE NOTICE '=== PUBLICATION COMPLETE ===';
    RAISE NOTICE 'Liverpool - Aston Villa published to week 44!';
    RAISE NOTICE 'Match ID: %, Analysis ID: %', v_match_id, v_analysis_id;
END $$;
