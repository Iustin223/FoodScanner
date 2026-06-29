import os
import uuid
import json
from fastapi import APIRouter, UploadFile, File, Request, Depends
from fastapi.templating import Jinja2Templates
from config import BASE_DIR, UPLOAD_DIR, ALLOWED_EXTENSIONS
from auth.deps import get_current_user_optional
from auth.models import User



templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "templates"))

router = APIRouter()

pipeline = None
parser = None
lookup = None


def load_models():

    global pipeline, parser, lookup

    if pipeline is not None:
        return
    print("Incarcare modele(prima rulare)...")

    from ocr.pipeline import RomanianOCRPipeline
    from ocr.parser import IngredientParser
    from ocr.lookup import IngredientLookUp

    pipeline = RomanianOCRPipeline()
    parser = IngredientParser()
    lookup = IngredientLookUp()

    print("Toate modelele sunt incarcate!")


@router.get("/")
def home(request : Request):
    return templates.TemplateResponse(
        request=request,
        name = "index.html"
    )    


@router.post("/scan")
async def scan_image(file: UploadFile = File(...), current_user: User | None = Depends(get_current_user_optional)):

    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        return {
            "error" : f"Format invalid ({ext}). Accepta: JPG, PNG, WEBP",
            "ingredients" : []
        }
        

    filename = f"{uuid.uuid4()}{ext}"
    filepath = str(UPLOAD_DIR / filename)

    content = await file.read()

    with open(filepath, "wb") as f:
        f.write(content)

    load_models()

    results = pipeline.process_image(filepath)
    if not results:
          return {
        "error": "Nu s-a detectat text în imagine. Încearcă cu o altă poză.",
        "ingredients": [],
        "image_url": f"/static/uploads/{filename}"
    }

    full_text = " ".join(line['text'] for line in results)

    ingredients = parser.parse(full_text)

    if not ingredients:
        return {
            "ocr_text": full_text,
            "error": "Nu s-au găsit ingrediente în text.",
            "ingredients": [],
            "image_url": f"/static/uploads/{filename}"
        }    

    scored = []
    for ing in ingredients:
        result = lookup.lookup(ing)
        scored.append(result)


    summary = {
        "periculos": 0,
        "moderat": 0,
        "inofensiv": 0,
        "necunoscut": 0
    }
    for item in scored:
        risk = item['risc']
        if risk in summary:
            summary[risk] += 1
    
    if current_user:
        try:
            
            from auth.models import ScanHistory
            from auth.database import get_session_direct


            session = get_session_direct()
            scan = ScanHistory(
                user_id=current_user.id,
                image_url=f"/static/uploads/{filename}",
                ocr_text=full_text,
                ingredients_json=json.dumps(scored, ensure_ascii=False),
                summary_json=json.dumps(summary, ensure_ascii=False),
            )

            session.add(scan)
            session.commit()
            session.refresh(scan)
            session.close()

        except Exception as e:
             print(f"[WARNING] Nu s-a putut salva în istoric: {e}")    



    # ─── STEP 8: RETURN JSON ───
    # FastAPI converts this dict to JSON automatically
    # The JavaScript fetch() call in app.js receives this
    # and calls displayResults(data) to show the cards
    return {
        "ocr_text": full_text,
        "ingredients": scored,
        "summary": summary,
        "image_url": f"/static/uploads/{filename}"
    }    


@router.get("/scan")
def scan_page(request: Request):
    return templates.TemplateResponse(request = request, name = "scan.html")

@router.get("/history")
def scan_page(request: Request):
    return templates.TemplateResponse(request = request, name = "history.html")









