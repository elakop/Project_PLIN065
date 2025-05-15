import asyncio
from playwright.async_api import async_playwright

class AjkaAnalyzer:
    def __init__(self, process_text):
        self.process_text = process_text

    async def AjkaSegmentation(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()

            # Open the page
            await page.goto("https://nlp.fi.muni.cz/projekty/wwwajka/WwwAjkaSkripty/morph.cgi?jazyk=0")

            # Wait for the form to load
            await page.wait_for_selector('form')

            # Select "segmentation" in the action field
            await page.click('input[type="radio"][name="akce"][value="2"]')        # segment
            await page.click('input[type="radio"][name="kodovani"][value="0"]')    # ISO-8859-2

            # Fill in the input sentence
            await page.fill('input[name="slovo"]', self.process_text)

            # Submit the form
            await page.click('input[type="submit"][value="Proveď"]')

            # Wait for the table to appear
            await page.wait_for_selector('table')

            # Extract the text from the table
            table = await page.locator('table').nth(0).inner_text()

            # Print the result (the whole table content)
            print(table)

            await browser.close()

async def main():
    analyzer = AjkaAnalyzer("Toto je sestovací věta")
    await analyzer.AjkaSegmentation()

asyncio.run(main())


