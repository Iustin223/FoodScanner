import pandas as pd
from PIL import Image
import torch
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from evaluate import load
import os
import evaluate


CSV_PATH = 'label_studio_data.csv'
IMAGE_DIR = 'dataset/dataset-crops-text-detection'

cer_metric = evaluate.load('cer')

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Folosesc {device}.  (Dacă scrie 'cuda', folosește RTX 4050!)")


    print("Descarcare model trOCR Fine Tuned...")
    processor = TrOCRProcessor.from_pretrained("trocr-model-romanian-final")
    model = VisionEncoderDecoderModel.from_pretrained("trocr-model-romanian-final")
    model.to(device)


    print("Citire csv...")
    df = pd.read_csv(CSV_PATH, encoding='utf-8')
    df = df.dropna(subset=['transcription'])

    if "image" in df.columns:
        df['file_name'] = df['image'].astype(str).str.replace('http://localhost:8081/', '', regex=False)
    else:
        print("Eroare. Nu se gaseste coloana 'image'  in CSV.")
        return

    test_samples = df.head(200) 

    predictions = []
    references = []

    print("\n" + "="*80)
    print(f"{'PREDICȚIE TrOCR DEFAULT (AI)':<40} | {'ADEVĂRUL (Scris de tine)'}")
    print("="*80)   

    for index, row in test_samples.iterrows():
        img_path = os.path.join(IMAGE_DIR, row['file_name'])
        adevar_uman = row['transcription']

        try:
            image = Image.open(img_path).convert("RGB")
            pixel_values = processor(image, return_tensors = "pt").pixel_values.to(device)
            generated_ids = model.generate(pixel_values)
            predictie = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            print(f"\n  Adevăr:     {adevar_uman}")
            print(f"  Fine-tuned: {predictie}")

            predictions.append(predictie)
            references.append(adevar_uman)

        except Exception as e:
            print(f"Eroare la poza {row['file_name']}: {e}")


    cer = cer_metric.compute(predictions=predictions, references=references)              
    print("\n" + "="*80)
    print(f"CER model baseline: {cer:.4f}")
    print("="*80)



if __name__ == "__main__":
    main()         