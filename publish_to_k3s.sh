#!/bin/bash
# Complete publication script for Liverpool - Aston Villa to k3s
# Includes: match, odds, analysis, and system suggestions

set -e  # Exit on error

echo "============================================================"
echo "PUBLISHING LIVERPOOL - ASTON VILLA TO K3S"
echo "============================================================"
echo ""

# Get PostgreSQL pod name (it might change)
echo "1. Finding PostgreSQL pod..."
POSTGRES_POD=$(sudo k3s kubectl get pods -n stryktips -l app=postgres -o jsonpath='{.items[0].metadata.name}')
echo "   Found: $POSTGRES_POD"
echo ""

# Copy SQL file to pod
echo "2. Copying SQL file to PostgreSQL pod..."
sudo k3s kubectl cp publish_to_k3s_complete.sql stryktips/$POSTGRES_POD:/tmp/publish_complete.sql
echo "   ✓ SQL file copied"
echo ""

# Execute SQL
echo "3. Executing SQL script..."
echo "   This will:"
echo "   - Deactivate week 43"
echo "   - Create week 44 coupon"
echo "   - Add Liverpool - Aston Villa"
echo "   - Add odds (1=1.57, X=4.75, 2=5.60)"
echo "   - Add analysis (recommended: 1, value: 1.22)"
echo "   - Add system suggestions (2 rows)"
echo ""
sudo k3s kubectl exec -n stryktips $POSTGRES_POD -- psql -U stryktips -d stryktips -f /tmp/publish_complete.sql
echo ""

# Verify publication
echo "4. Verifying publication..."
echo ""
echo "   Checking coupons:"
sudo k3s kubectl exec -n stryktips $POSTGRES_POD -- psql -U stryktips -d stryktips -c "
SELECT
    c.week_number,
    c.year,
    c.is_active,
    COUNT(m.id) as match_count
FROM coupons c
LEFT JOIN matches m ON c.id = m.coupon_id
GROUP BY c.id, c.week_number, c.year, c.is_active
ORDER BY c.week_number DESC
LIMIT 5;
"
echo ""

echo "   Checking Liverpool match:"
sudo k3s kubectl exec -n stryktips $POSTGRES_POD -- psql -U stryktips -d stryktips -c "
SELECT
    m.match_number,
    m.home_team,
    m.away_team,
    m.home_percentage,
    o.home_odds,
    o.draw_odds,
    o.away_odds,
    a.recommended_signs,
    a.home_value
FROM matches m
JOIN coupons c ON m.coupon_id = c.id
LEFT JOIN odds o ON m.id = o.match_id
LEFT JOIN analyses a ON m.id = a.match_id
WHERE c.week_number = 44
ORDER BY m.match_number;
"
echo ""

echo "   Checking system suggestions:"
sudo k3s kubectl exec -n stryktips $POSTGRES_POD -- psql -U stryktips -d stryktips -c "
SELECT
    half_cover_count,
    expected_value,
    cost_factor,
    reasoning
FROM suggested_rows sr
JOIN coupons c ON sr.coupon_id = c.id
WHERE c.week_number = 44
ORDER BY expected_value DESC;
"
echo ""

# Test the web interface
echo "5. Testing web interface..."
echo "   Waiting 2 seconds for cache to clear..."
sleep 2

# Get the ingress host
INGRESS_HOST=$(sudo k3s kubectl get ingress -n stryktips stryktips-ingress -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "stryktips.local")

echo "   Checking http://$INGRESS_HOST/..."
if curl -s "http://$INGRESS_HOST/" | grep -q "Liverpool"; then
    echo "   ✓ Liverpool found on homepage!"
else
    echo "   ⚠ Warning: Liverpool not found on homepage yet. Try refreshing your browser."
fi
echo ""

echo "============================================================"
echo "PUBLICATION COMPLETE!"
echo "============================================================"
echo ""
echo "✅ Liverpool - Aston Villa is now published!"
echo ""
echo "📊 Summary:"
echo "   - Week: 44, 2025"
echo "   - Match: Liverpool vs Aston Villa"
echo "   - Odds: 1=1.57, X=4.75, 2=5.60"
echo "   - Recommendation: 1 (hemmavinst)"
echo "   - Value: 1.22 (+22% value!)"
echo "   - System rows: 2 generated"
echo ""
echo "🌐 View at: http://$INGRESS_HOST/"
echo ""
echo "💡 Analysis highlights:"
echo "   - Liverpool has 62.1% win probability (vs 51% from Swedish public)"
echo "   - Strong value bet on '1' with 22% edge"
echo "   - Suggested row 2 with '1X' hedge has higher expected value (0.17)"
echo ""
