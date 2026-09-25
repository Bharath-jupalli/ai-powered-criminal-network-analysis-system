<<<<<<< HEAD
# AI Criminal Investigation System — Enhanced Prototype

A synthetic/demo investigator-assistance prototype for the hackathon.

## Added modules

- Previous Case Intelligence
  - Upload previous case PDF/DOCX/TXT files.
  - Extract persons/entities, locations, vehicles, phones and accounts using the existing FIR parser.
  - Compare historical files with the selected current case.
  - Surface overlaps in mentioned people/entities, locations, vehicles, communication/financial identifiers and incident-pattern indicators.
  - Show explainable correlation reasons.
- CCTV Intelligence
  - Upload MP4 CCTV footage.
  - Store and preview uploaded footage.
  - Sample frames and report observable movement/person-detection events using OpenCV HOG.
  - Uses anonymous observations; no face identification.
- Cyber/scientific dashboard styling and investigation-oriented navigation.

## Run on Windows

```bat
cd C:\Users\jagad\OneDrive\Desktop\criminal-network-ai
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app
```

Open `http://127.0.0.1:8000`

Use `uvicorn main:app` rather than `--reload` if the virtual environment is inside the project folder.

## Demo data and safety

Use only synthetic/demo case files for the hackathon. Historical matches and CCTV observations are analytical leads for investigator review; they do not establish identity, guilt, or criminal involvement.

CCTV analysis requires `opencv-python-headless`. Large videos may take time to process because frame analysis is CPU-based.
=======
# ai-powered-criminal-network-analysis-system
>>>>>>> 7baad692feb46ad92a2431d2c65f7ecf3d37a0c1
