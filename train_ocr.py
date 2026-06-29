import os
import pandas as pd
import torch
from torch.utils.data import Dataset
from PIL import Image
from sklearn.model_selection import train_test_split
from transformers import (
    TrOCRProcessor, 
    VisionEncoderDecoderModel, 
    Seq2SeqTrainer, 
    Seq2SeqTrainingArguments,
    default_data_collator
)
import evaluate

# --- CONFIGURARE ---
CSV_PATH = 'label_studio_data.csv'
IMAGE_DIR = 'dataset/dataset-crops-text-detection'
MODEL_NAME = "microsoft/trocr-base-printed"

cer_metric = evaluate.load("cer")

def compute_metrics(pred):
    labels_ids = pred.label_ids
    pred_ids = pred.predictions

    # Daca predictiile sunt logits (3D), luam argmax
    if len(pred_ids.shape) == 3:
        pred_ids = pred_ids.argmax(axis=-1)

    labels_ids[labels_ids == -100] = processor.tokenizer.pad_token_id

    pred_str = processor.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = processor.batch_decode(labels_ids, skip_special_tokens=True)

    cer = cer_metric.compute(predictions=pred_str, references=label_str)
    return {"cer": cer}

class RomanianOCRDataset(Dataset):
    def __init__(self, df, processor, max_target_length=128):
        self.df = df.reset_index(drop=True)
        self.processor = processor
        self.max_target_length = max_target_length

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        file_name = self.df['file_name'][idx]
        text = self.df['transcription'][idx]
        
        img_path = os.path.join(IMAGE_DIR, file_name)
        image = Image.open(img_path).convert("RGB")
        
        pixel_values = self.processor(image, return_tensors="pt").pixel_values.squeeze()
        
        labels = self.processor.tokenizer(
            text, 
            padding="max_length", 
            max_length=self.max_target_length, 
            truncation=True
        ).input_ids
        
        labels = [label if label != self.processor.tokenizer.pad_token_id else -100 for label in labels]
        
        return {"pixel_values": pixel_values, "labels": torch.tensor(labels)}

if __name__ == "__main__":
    print("Incarcam modelul si procesorul...")
    processor = TrOCRProcessor.from_pretrained(MODEL_NAME)
    model = VisionEncoderDecoderModel.from_pretrained(MODEL_NAME)

    # Parametri pentru decodor
    model.config.decoder_start_token_id = processor.tokenizer.cls_token_id
    model.config.pad_token_id = processor.tokenizer.pad_token_id
    model.config.vocab_size = model.config.decoder.vocab_size
    model.config.eos_token_id = processor.tokenizer.sep_token_id
    model.generation_config.max_length = 128
    model.generation_config.early_stopping = True
    model.generation_config.length_penalty = 2.0
    model.generation_config.num_beams = 4
    # REMOVED: no_repeat_ngram_size — food labels repeat phrases naturally

    print("Pregatim dataset-ul...")
    df = pd.read_csv(CSV_PATH, encoding='utf-8')
    df = df.dropna(subset=['transcription'])
    if 'image' in df.columns:
        df['file_name'] = df['image'].astype(str).str.replace('http://localhost:8081/', '', regex=False)
    
    train_df, eval_df = train_test_split(df, test_size=0.10, random_state=42)
    
    train_dataset = RomanianOCRDataset(train_df, processor)
    eval_dataset = RomanianOCRDataset(eval_df, processor)
    
    print(f"Date de antrenament: {len(train_dataset)} | Date de validare: {len(eval_dataset)}")

    training_args = Seq2SeqTrainingArguments(
        output_dir="./trocr-model-romanian",
        predict_with_generate=True,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=10,
        per_device_train_batch_size=2,
        per_device_eval_batch_size=2,
        fp16=True,
        num_train_epochs=10,           
        learning_rate=4e-5,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="cer",
        greater_is_better=False,
        generation_max_length=128,      
    )

    trainer = Seq2SeqTrainer(
        model=model,
        processing_class=processor,     
        args=training_args,
        compute_metrics=compute_metrics,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=default_data_collator,
    )

    print("Incepem antrenamentul (Fine-Tuning)!")
    trainer.train()
    
    trainer.save_model("./trocr-model-romanian-final")
    processor.save_pretrained("./trocr-model-romanian-final")
    print("Antrenamentul a fost completat cu succes! Modelul tau este gata.")