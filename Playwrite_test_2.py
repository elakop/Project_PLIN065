import asyncio
from playwright.async_api import async_playwright
import aiofiles
import re

class AjkaAnalyzer:
    def __init__(self, process_text):
        self.process_text = process_text

    async def AjkaSegmentation(self):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)  # False for finetuning
            page = await browser.new_page()

            await page.goto("https://nlp.fi.muni.cz/projekty/wwwajka/WwwAjkaSkripty/morph.cgi?jazyk=0")
            await page.wait_for_selector('form')

            await page.click('input[type="radio"][name="akce"][value="2"]')        # segmentace
            await page.click('input[type="radio"][name="kodovani"][value="0"]')    # ISO-8859-2
            await page.fill('input[name="slovo"]', self.process_text)
            await page.click('input[type="submit"][value="Proveď"]')
            await page.wait_for_selector('table')

            table = await page.locator('table').nth(0).inner_text()

            await browser.close()
            return table

async def process_file(input_path: str, output_path: str):
    async with aiofiles.open(input_path, mode='r', encoding='utf-8') as infile, \
               aiofiles.open(output_path, mode='w', encoding='utf-8') as outfile:

        line_number = 0
        async for line in infile:
            sentence = re.sub(r'[.?!…]+$', '', line.strip())
            if not sentence:
                continue

            print(f"Zpracovávám větu {line_number}: {sentence[:50]}...")

            analyzer = AjkaAnalyzer(sentence)
            try:
                result = await analyzer.AjkaSegmentation()
                await outfile.write(f"--- Věta {line_number} ---\n")
                await outfile.write(result + "\n\n")
            except Exception as e:
                print(f"Chyba u věty {line_number}: {e}")
                await outfile.write(f"--- Věta {line_number} - chyba ---\n{e}\n\n")

            line_number += 1

if __name__ == "__main__":
    input_txt = "segmented_sample.txt"        #csTenTen2017_sentences_not_on_seperate_lines is 4GB text file
    output_txt = "vystup_ajka.txt"      # output file
    asyncio.run(process_file(input_txt, output_txt))
