import asyncio
from playwright.async_api import async_playwright
import aiofiles
import re

class AjkaAnalyzer:
    async def _init_(self):
        self.playwright = await async_playwright().start() #so "async with async_playwright() as p:" is not needed in every def 
        self.browser = await self.playwright.chromium.launch(headless=True)  # False for finetuning
        self.page = await self.browser.new_page()

    async def clean_up(self):
        await self.browser.close()
        await self.playwright.stop()

    async def segment(self, text):
        await self.page.goto("https://nlp.fi.muni.cz/projekty/wwwajka/WwwAjkaSkripty/morph.cgi?jazyk=0")
        await self.page.wait_for_selector('form')

        await self.page.click('input[type="radio"][name="akce"][value="2"]')        # segmentace
        await self.page.click('input[type="radio"][name="kodovani"][value="0"]')    # ISO-8859-2
        await self.page.fill('input[name="slovo"]', text)
        await self.page.click('input[type="submit"][value="Proveď"]')
        await self.page.wait_for_selector('table')

        table = await self.page.locator('table').nth(0).inner_text()
        await asyncio.sleep(2)
        return table

async def process_file(input_path: str, output_path: str):
    async with aiofiles.open(input_path, mode='r', encoding='utf-8') as infile, \
               aiofiles.open(output_path, mode='w', encoding='utf-8') as outfile:#input opens segmented_sample(later 4GB file) and output opens "výstup_Ajka"
    
        analyzer = AjkaAnalyzer()
        await analyzer._init_()

        line_number = 0
        async for line in infile:
            sentence = re.sub(r'[.?!…]+$', '', line.strip()) #deletes dot and blank spaces
            if not sentence:
                continue

            print(f"Zpracovávám větu {line_number}: {sentence[:50]}...")

            
            try:
                result = await analyzer.segment(sentence)
                await outfile.write(f"--- Věta {line_number} ---\n")
                await outfile.write(result + "\n\n")
            except Exception as e:
                print(f"Chyba u věty {line_number}: {e}")
                await outfile.write(f"--- Věta {line_number} - chyba ---\n{e}\n\n")

            line_number += 1

        analyzer.clean_up()

if __name__ == "__main__":
    input_txt = "segmented_sample.txt"        #csTenTen2017_sentences_not_on_seperate_lines is 4GB text file
    output_txt = "vystup_ajka.txt"      # výstupní soubor
    asyncio.run(process_file(input_txt, output_txt))
