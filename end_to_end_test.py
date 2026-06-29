import os
import cv2
import numpy as np
import torch 
from PIL import Image
from paddleocr import TextDetection
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

MODEL_PATH = "trocr-model-romanian-final"

print("Incarcare model PaddleOCR pentru detectie si TrOCR-ul pentru recunoastere...")


class RomanianOCRPipeline():
    def __init__(self, model_path = MODEL_PATH):
        
        self.detector = TextDetection()

        print("Incarcare model fine tune TrOCR! ...")

        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = TrOCRProcessor.from_pretrained(model_path)
        self.model = VisionEncoderDecoderModel.from_pretrained(model_path)
        self.model.to(self.device)
        self.model.eval()
        print(f"Pipeline complet!, Device {self.device}")


    def order_points(self, pts):
        rect = np.zeros((4, 2), dtype='float32')
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]
        return rect

    def get_perspective(self, image, pts):
        rect = self.order_points(np.array(pts, dtype="float32"))
        (tl, tr, br, bl) = rect

        widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        maxWidth = max(int(widthA), int(widthB))

        heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        maxHeight = max(int(heightA), int(heightB))        

        if maxWidth < 10 or maxHeight < 5:
            return None

        dst = np.array([
            [0, 0],
            [maxWidth - 1, 0],
            [maxWidth - 1, maxHeight - 1],
            [0, maxHeight - 1]
        ], dtype='float32')

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
        return warped
    
    def recognize_crop(self, crop_image):
        pil_image = Image.fromarray(cv2.cvtColor(crop_image, cv2.COLOR_BGR2RGB))
        pixel_values = self.processor(pil_image, return_tensors="pt").pixel_values.to(self.device)

        with torch.no_grad():
            output = self.model.generate(
                pixel_values, 
                output_scores=True, 
                return_dict_in_generate=True
            )

        text = self.processor.batch_decode(output.sequences, skip_special_tokens=True)[0]

        if output.scores:
            import torch.nn.functional as F
            probs = [F.softmax(score, dim=-1).max().item() for score in output.scores]
            confidence = sum(probs) / len(probs) if probs else 0
        else:
            confidence = 0

        return text, confidence
    

    def process_image(self, image_path):
        image = cv2.imread(image_path)
        if image is None:
            print(f"Eroare: nu pot citi imaginea {image_path}")
            return []

        results = self.detector.predict(os.path.abspath(image_path))  

        if not results:
            print("Nu s-a detectat text în imagine.")
            return []      

        lines = []

        for res in results:
            polys = res.get("dt_polys", [])
            if polys is None or (hasattr(polys, '__len__') and len(polys) == 0):
                polys = getattr(res, 'dt_polys', [])

           
            if polys is not None and len(polys) > 0:
                polys = sorted(polys, key=lambda box: np.array(box)[:, 1].min())

            for box in polys:
                crop = self.get_perspective(image, box)
                if crop is None:
                    continue
                
                h, w = crop.shape[:2]

                # Skip tiny crops
                if w < 30 or h < 10:
                    continue
                
                # Skip nearly-square crops (logos, icons)
                if w / h < 1.5:
                    continue
                
                text, confidence = self.recognize_crop(crop)

                if len(text.strip()) < 2:
                    continue

                if confidence < 0.7:
                    continue
                
               
                if text.strip().replace(' ', '').isdigit():
                    continue

                lines.append({
                    'text': text,
                    'box': box.tolist() if hasattr(box, 'tolist') else box
                })

        return lines


def main():
    pipeline = RomanianOCRPipeline()
    
    
    import sys
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = input("Calea către imagine: ")
    
    print(f"\nProcesez: {image_path}")
    print("=" * 80)
    
    results = pipeline.process_image(image_path)
    
    if not results:
        print("Nu s-a detectat text.")
        return
    
    
    full_text = []
    for i, line in enumerate(results):
        print(f"  Linia {i+1}: {line['text']}")
        full_text.append(line['text'])
    
    
    print("=" * 80)
    print("\nTEXT COMPLET EXTRAS:")
    print(" ".join(full_text))


if __name__ == "__main__":
    main()       