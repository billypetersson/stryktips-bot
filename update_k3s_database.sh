#!/bin/bash
# Script to add Liverpool - Aston Villa to k3s PostgreSQL database

echo "=== Updating k3s PostgreSQL Database ==="
echo ""

# Copy SQL file to postgres pod
echo "1. Copying SQL file to PostgreSQL pod..."
sudo k3s kubectl cp add_liverpool_k3s.sql stryktips/postgres-7994cb9d77-lpc5k:/tmp/add_liverpool.sql

# Execute SQL
echo "2. Executing SQL..."
sudo k3s kubectl exec -n stryktips postgres-7994cb9d77-lpc5k -- psql -U stryktips -d stryktips -f /tmp/add_liverpool.sql

# Verify
echo ""
echo "3. Verifying data..."
sudo k3s kubectl exec -n stryktips postgres-7994cb9d77-lpc5k -- psql -U stryktips -d stryktips -c "
SELECT
    c.week_number,
    c.year,
    c.is_active,
    COUNT(m.id) as match_count
FROM coupons c
LEFT JOIN matches m ON c.id = m.coupon_id
GROUP BY c.id, c.week_number, c.year, c.is_active
ORDER BY c.week_number DESC;
"

echo ""
echo "4. Checking Liverpool match..."
sudo k3s kubectl exec -n stryktips postgres-7994cb9d77-lpc5k -- psql -U stryktips -d stryktips -c "
SELECT
    m.match_number,
    m.home_team,
    m.away_team,
    m.home_percentage,
    o.home_odds,
    o.draw_odds,
    o.away_odds
FROM matches m
JOIN coupons c ON m.coupon_id = c.id
LEFT JOIN odds o ON m.id = o.match_id
WHERE c.week_number = 44
ORDER BY m.match_number;
"

echo ""
echo "=== Done! Check http://stryktips.local/ ==="
