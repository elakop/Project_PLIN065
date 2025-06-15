import asyncio
from playwright.async_api import async_playwright
import aiofiles
import re

class AjkaAnalyzer:
    def __init__(self): #init can't be async
        self.playwright = None
        self.browser = None
        self.page = None
    
    async def initialize(self):
        self.playwright = await async_playwright().start() #so "async with async_playwright() as p:" is not needed in every def 
        self.browser = await self.playwright.chromium.launch(headless=True)  # False for finetuning
        self.page = await self.browser.new_page()

    async def clean_up(self):
        if self.browser: #safety feature: clean_up might be called before the browser is created (self.browser=None)
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    def clean_text(self, text):
        #special characters and dots
        cleaned = re.sub(r'[()[\]:;_\'\"„"…/\\&%@#+=><=|~`€$£*^.?!-,]', ' ', text)
        #numbers
        cleaned = re.sub(r'\d+', ' ', cleaned)
        #multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned

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

    async def table_to_dic(self,table_text):
        morphemed = {}
        lines = table_text.strip().split('\n')
        
        start_processing = False
        for line in lines:
            line = line.strip()
            
            if not line:
                continue

            if line.startswith('Analyzovaný tvar'):
                start_processing = True
                continue
            
            if not start_processing:
                continue
            
            parts = line.split('\t')
            if len(parts) >= 8:#Analyzovaný tvar | Základní tvar(y) | | Prefix | Kmenový základ | Intersegment | Koncovka | Postfix
                word = parts[0].strip()
                prefix = parts[3].strip()
                root_base = parts[4].strip()
                intersegment = parts[5].strip()
                suffix = parts[6].strip()
                postffix = parts[7].strip()

                if not word or word == '-':
                    continue

                segmentation_parts = []
                if prefix and prefix != '-':
                    segmentation_parts.append(prefix)
                
                if root_base and root_base != '-':
                    segmentation_parts.append(root_base)
                
                if intersegment and intersegment != '-':
                    segmentation_parts.append(intersegment)
                
                if suffix and suffix != '-':
                    segmentation_parts.append(suffix)

                if postffix and postffix != '-':
                    segmentation_parts.append(postffix)
                
                if segmentation_parts:
                    segmentation = '-'.join(segmentation_parts)
                    morphemed[word] = segmentation #[key], segmentation = value

        return morphemed 

async def process_file(input_path: str, output_path: str):
    analyzer = AjkaAnalyzer()
    await analyzer.initialize()

    try:
        async with aiofiles.open(input_path, mode='r', encoding='utf-8') as infile, \
                   aiofiles.open(output_path, mode='w', encoding='utf-8') as outfile: #input opens segmented_sample(later 4GB file) and output opens "výstup_Ajka"

            line_number = 0
            async for line in infile:
                sentence = analyzer.clean_text(line.strip())
                if not sentence:
                    continue

                print(f"Zpracovávám větu {line_number}: {sentence[:50]}...")

            
                try:
                    result = await analyzer.segment(sentence)
                    morphological_data = await analyzer.table_to_dic(result)
                    await outfile.write(f"--- Věta {line_number} ---\n")
                    for word, segmentation in morphological_data.items():
                        await outfile.write(f"{word}: {segmentation}; ")
                    await outfile.write("\n\n")

                except Exception as e:
                    print(f"Chyba u věty {line_number}: {e}")
                    await outfile.write(f"--- Věta {line_number} - chyba ---\n{e}\n\n")

                line_number += 1
    
    finally:       
        await analyzer.clean_up()

if __name__ == "__main__":
    input_txt = "segmented_sample.txt"        #csTenTen2017_sentences_not_on_seperate_lines is 4GB text file
    output_txt = "vystup_ajka.txt"      # output file
    asyncio.run(process_file(input_txt, output_txt))
