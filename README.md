# OCR-corrector

##

-

#### Set up:

- 1. Download or clone this repository.

```
git clone https://github.com/lp-hub/
```

- 2. Install GCC / build tools

```
sudo apt update

sudo apt install python3 python3.12-venv build-essential cmake sqlite3

sudo apt install calibre djvulibre-bin libchm-bin pandoc tesseract-ocr-all
```

- 3. Create and activate virtual environment

```
cd /../OCR-corrector && python3.12 -m venv venv # to create venv dir

source venv/bin/activate # (venv) USER@PC:/../OCR-corrector$

deactivate # after usig RAG
```

- 4. Install Python dependencies

```
pip install --upgrade pip && pip3 install striprtf

pip install ftfy langchain langchain-community langchain-huggingface pathspec pillow pymupdf pypandoc pypdf pyrtf-ng pyspellchecker pytesseract python-docx python-dotenv rapidfuzz sentence-transformers sqlite-utils symspellpy tiktoken unstructured
```

- 5.

```

```

- 6. Download

```

```

- 7. Add your documents

```
Place .pdf, .txt, .md, .epub, etc., into your files/ folder.
Supported file types are automatically handled by the loader.
```

- 8. Create and onfigure .env, edit scripts

```

```

#### Usage
```
1. Run the CLI interface

python3 main.py


2. (Optional) Start Web UI

python3 webui.py


```
#### Notes

