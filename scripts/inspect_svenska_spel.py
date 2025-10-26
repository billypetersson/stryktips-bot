"""
Script för att inspektera Svenska Spels webbplats och hitta rätt selektorer.
Detta script öppnar sidan, väntar på att den laddats, och visar HTML-strukturen.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright


async def inspect_page():
    """Inspect Svenska Spel page structure."""
    async with async_playwright() as p:
        print("\n🌐 Startar webbläsare (headless)...")
        browser = await p.chromium.launch(
            headless=True,  # Headless för server utan display
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )

        try:
            page = await browser.new_page()

            print("📡 Laddar Svenska Spel Stryktips-sidan...")
            await page.goto('https://spela.svenskaspel.se/stryktipset', wait_until='networkidle', timeout=60000)

            print("⏳ Väntar 5 sekunder så att allt hinner laddas...")
            await asyncio.sleep(5)

            # Ta screenshot för debugging
            await page.screenshot(path='stryktipset_screenshot.png')
            print("📸 Screenshot sparad som: stryktipset_screenshot.png")

            # Hämta sidans titel
            title = await page.title()
            print(f"\n📄 Sidtitel: {title}")

            # Leta efter olika möjliga match-element
            print("\n🔍 Letar efter match-element...")

            # Test 1: Leta efter events/matcher med olika selektorer
            selectors_to_try = [
                'article',
                '[data-testid*="event"]',
                '[class*="event"]',
                '[class*="match"]',
                '[class*="game"]',
                'tbody tr',
                '.coupon-event',
                '.match-row',
                '.event-row',
            ]

            for selector in selectors_to_try:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        print(f"✓ Hittade {len(elements)} element med selector: '{selector}'")

                        # Visa HTML för första elementet
                        if len(elements) > 0:
                            first_html = await elements[0].inner_html()
                            print(f"  Första elementets HTML (första 200 tecken):")
                            print(f"  {first_html[:200]}...")
                except Exception as e:
                    print(f"✗ Selector '{selector}' fungerade inte: {e}")

            # Försök hitta alla klasser på sidan
            print("\n📋 Alla unika CSS-klasser på sidan:")
            all_classes = await page.evaluate("""
                () => {
                    const elements = document.querySelectorAll('*');
                    const classes = new Set();
                    elements.forEach(el => {
                        if (el.className && typeof el.className === 'string') {
                            el.className.split(' ').forEach(c => {
                                if (c && (c.includes('event') || c.includes('match') || c.includes('game') || c.includes('coupon'))) {
                                    classes.add(c);
                                }
                            });
                        }
                    });
                    return Array.from(classes).sort();
                }
            """)
            for cls in all_classes[:20]:  # Visa första 20
                print(f"  - {cls}")

            # Försök extrahera data med JavaScript
            print("\n💡 Försöker extrahera matchdata med JavaScript...")
            match_data = await page.evaluate("""
                () => {
                    // Försök hitta alla event/match-element
                    const possibleSelectors = [
                        'article',
                        '[data-testid*="event"]',
                        'tbody tr',
                        '.event',
                        '.match'
                    ];

                    for (const selector of possibleSelectors) {
                        const elements = document.querySelectorAll(selector);
                        if (elements.length > 5) { // Stryktipset har 13 matcher
                            const data = [];
                            elements.forEach((el, idx) => {
                                const text = el.textContent || '';
                                if (text.length > 10 && idx < 5) { // Bara första 5 för inspection
                                    data.push({
                                        selector: selector,
                                        index: idx,
                                        text: text.substring(0, 100),
                                        html: el.outerHTML.substring(0, 200)
                                    });
                                }
                            });
                            if (data.length > 0) {
                                return data;
                            }
                        }
                    }
                    return [];
                }
            """)

            if match_data:
                print(f"✓ Hittade {len(match_data)} potentiella matcher:")
                for m in match_data:
                    print(f"\n  Match {m['index']} (selector: {m['selector']}):")
                    print(f"    Text: {m['text']}")
                    print(f"    HTML: {m['html']}...")
            else:
                print("✗ Kunde inte extrahera matchdata automatiskt")

            # Spara sidans HTML
            html_content = await page.content()
            with open('stryktipset_page.html', 'w', encoding='utf-8') as f:
                f.write(html_content)
            print("\n💾 Fullständig HTML sparad som: stryktipset_page.html")

        finally:
            await browser.close()
            print("\n✅ Klar!")


if __name__ == "__main__":
    asyncio.run(inspect_page())
