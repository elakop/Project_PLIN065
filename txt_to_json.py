import json
import re

def parse_ajka(input_file, output_file): #converts txt to json

    data = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    #dividing into sentences
    parts = re.split(r'--- Věta \d+ ---', text)
    
    sentences = 0
    words = 0
    
    for part in parts:
        part = part.strip()
        
        if not part:
            continue
            
        sentences += 1
        
        # pair of "word:segmentation"
        pairs = re.findall(r'([^:;]+?):\s*([^:;]+?);', part)
        
        for word, seg in pairs:
            word = word.strip()
            seg = seg.strip()
            
            if not word or not seg or word == '-' or seg == '-':
                continue
            
            morph = seg.split('-') if '-' in seg else [seg]
            
            item = {
                "word": word,
                "segmentation": seg,
                "morphemes": morph
            }
            
            data.append(item)
            words += 1
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Vět: {sentences}")
    print(f"Slov: {words}")

if __name__ == "__main__":

    input_txt = "vystup_ajka.txt"
    output_json = "dataset.json"

    parse_ajka(input_txt, output_json)