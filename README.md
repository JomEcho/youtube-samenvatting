# YouTube Samenvatting

Een macOS desktop applicatie die automatisch samenvattingen maakt van YouTube video's (met name podcasts) door gebruik te maken van de automatische transcripties van YouTube en AI taalmodellen.

## Wat doet deze app?

1. **Haalt de transcriptie op** van een YouTube video (de automatische ondertiteling)
2. **Maakt een samenvatting** met een AI taalmodel naar keuze
3. **Slaat beide op** als bestanden in een map op je computer
4. **Chat over de video** - stel vervolgvragen over de inhoud (antwoorden gebaseerd op het transcript)

## Installatie

### Vereisten

- macOS (getest op macOS 14 Sonoma)
- Python 3.13 met tkinter (`brew install python-tk@3.13`)
- API keys voor OpenAI en/of Anthropic (of lokale Ollama installatie)

### Stappen

```bash
# 1. Ga naar de project map
cd /Users/jom/Documents/Kode/youtube-samenvatting

# 2. Maak virtual environment aan (eenmalig)
/opt/homebrew/bin/python3.13 -m venv venv

# 3. Activeer virtual environment
source venv/bin/activate

# 4. Installeer dependencies
pip install -r requirements.txt

# 5. Configureer API keys in .env bestand
# (zie sectie "API Keys Configuratie" hieronder)

# 6. Start de app
python gui_app.py
```

### Desktop App

Er is een `.app` bundle gemaakt die je kunt dubbelklikken:

**Locatie:** `~/Desktop/YouTube Samenvatting.app`

Deze app roept het Python script aan, dus de virtual environment moet bestaan.

---

## API Keys Configuratie

De app gebruikt een `.env` bestand voor de API keys. Dit bestand staat in `.gitignore` en wordt nooit gecommit naar git.

### Bestand: `.env`

```
OPENAI_API_KEY=sk-proj-xxx...
ANTHROPIC_API_KEY=sk-ant-xxx...
```

### Waar haal je API keys vandaan?

- **OpenAI:** https://platform.openai.com/api-keys
- **Anthropic:** https://console.anthropic.com/settings/keys

Je hebt speciale keys aangemaakt genaamd "YTsum" voor dit project.

---

## Gebruik

1. **Start de app** (dubbelklik op Desktop of `python gui_app.py`)
2. **Plak een YouTube URL** in het invoerveld
3. **Kies een taalmodel:**
   - Ollama - gpt-oss:20b (lokaal, gratis, max ~3 uur video)
   - Ollama - gemma2:9b (lokaal, gratis, max ~30 min video)
   - OpenAI GPT-4o-mini (snel, betaald per gebruik)
   - Anthropic Claude Sonnet 4 (snel, betaald per gebruik)
4. **Klik "Samenvatting Maken"**
5. **Bestanden verschijnen** in `~/Documents/YouTube-Samenvattingen/`
6. **Chat over de video** - na de samenvatting wordt de Chat knop actief. Stel vragen over de video en krijg antwoorden gebaseerd op het transcript (het model verzint niets)

### Output bestanden

Voor elke video worden twee bestanden gemaakt:

```
20241229_093045_Video_Titel_transcriptie.txt   # Ruwe transcriptie
20241229_093045_Video_Titel_samenvatting.docx  # AI samenvatting (Word document)
```

### Chat functie

Na het maken van een samenvatting kun je vragen stellen over de video:

- De **Chat knop** wordt actief zodra een samenvatting klaar is
- Stel vragen in het Nederlands over de inhoud van de video
- Het model baseert antwoorden **alleen** op het transcript
- Als iets niet in de video staat, zegt het model: "Dit staat niet in de video"
- De chat gebruikt automatisch hetzelfde model als de samenvatting

---

## Projectstructuur

```
youtube-samenvatting/
├── .env                    # API keys (NIET in git)
├── .env.example            # Voorbeeld .env bestand
├── .gitignore              # Bestanden die git negeert
├── requirements.txt        # Python dependencies
├── youtube_samenvatting.py # Hoofdmodule met alle logica
├── gui_app.py              # Grafische interface (tkinter)
├── build_app.py            # Script om .app te bouwen
├── create_macos_app.sh     # Script om desktop app te maken
├── setup.sh                # Installatie script
└── README.md               # Dit bestand
```

---

## Hoe werkt het? (Technische uitleg)

### 1. youtube_samenvatting.py - De kern van de applicatie

Dit bestand bevat alle logica:

#### Imports en configuratie (regels 1-27)

```python
from youtube_transcript_api import YouTubeTranscriptApi  # Haalt YouTube transcripties op
from dotenv import load_dotenv  # Laadt .env bestand
import requests  # Voor HTTP requests naar Ollama
```

#### `extract_video_id(url)` - Video ID extraheren

```python
def extract_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
        r'^([a-zA-Z0-9_-]{11})$'
    ]
```

**Wat doet het?**
- Accepteert verschillende YouTube URL formaten:
  - `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
  - `https://youtu.be/dQw4w9WgXcQ`
  - `https://youtube.com/embed/dQw4w9WgXcQ`
- Extraheert de 11-karakter video ID met regex (regular expressions)
- Regex `[a-zA-Z0-9_-]{11}` betekent: precies 11 karakters van letters, cijfers, underscore of streepje

#### `get_video_title(video_id)` - Titel ophalen

```python
def get_video_title(video_id: str) -> str:
    response = requests.get(f"https://www.youtube.com/watch?v={video_id}")
    match = re.search(r'<title>(.+?) - YouTube</title>', response.text)
```

**Wat doet het?**
- Haalt de YouTube pagina op als gewone HTML
- Zoekt de `<title>` tag met regex
- Verwijdert ongeldige bestandsnaam karakters voor veilig opslaan

#### `get_transcript(video_id)` - Transcriptie ophalen

```python
def get_transcript(video_id: str) -> Tuple[str, str]:
    api = YouTubeTranscriptApi()
    transcript_list = list(api.list(video_id))

    # Prioriteit: Nederlands > Engels > Andere
    priority = ['nl', 'en']

    data = api.fetch(video_id, languages=[lang])
    full_text = "\n".join([entry.text for entry in data])
```

**Wat doet het?**
- Gebruikt de `youtube-transcript-api` library
- Vraagt beschikbare transcripties op
- Kiest Nederlands als het beschikbaar is, anders Engels
- Voegt alle tekst fragmenten samen tot één string

#### `summarize_with_openai(text, api_key)` - OpenAI samenvatting

```python
def summarize_with_openai(text: str, api_key: str) -> str:
    from openai import OpenAI
    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": f"TRANSCRIPTIE:\n{text[:100000]}"}
        ],
        temperature=0.3,
        max_tokens=2000
    )
```

**Wat doet het?**
- Maakt verbinding met OpenAI API
- Stuurt de transcriptie naar GPT-4o-mini
- `temperature=0.3` zorgt voor consistente, minder "creatieve" output
- `max_tokens=2000` beperkt de lengte van de samenvatting
- `text[:100000]` beperkt de input tot 100K karakters (API limiet)

#### `summarize_with_anthropic(text, api_key)` - Anthropic samenvatting

```python
def summarize_with_anthropic(text: str, api_key: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": f"{prompt}\n\n---\nTRANSCRIPTIE:\n{text[:150000]}"}]
    )
```

**Wat doet het?**
- Vergelijkbaar met OpenAI, maar voor Anthropic's Claude
- Claude kan langere context aan (150K karakters)
- Gebruikt Claude Sonnet 4 model

#### `summarize_with_ollama(text, model)` - Lokale Ollama samenvatting

```python
def summarize_with_ollama(text: str, model: str = "gpt-oss:20b") -> str:
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 2000}
        },
        timeout=300
    )
```

**Wat doet het?**
- Praat met lokale Ollama server via HTTP POST
- Ollama draait op `localhost:11434`
- `stream=False` wacht tot hele response klaar is
- Timeout van 5 minuten omdat lokale modellen langzamer zijn

#### `process_video(url, provider, api_key)` - Hoofdfunctie

```python
def process_video(url, provider, api_key, progress_callback=None):
    video_id = extract_video_id(url)
    title = get_video_title(video_id)
    transcript, lang = get_transcript(video_id)
    summary = summarize(transcript, provider, api_key)

    # Sla bestanden op
    transcript_path = OUTPUT_DIR / f"{timestamp}_{safe_title}_transcriptie.txt"
    summary_path = OUTPUT_DIR / f"{timestamp}_{safe_title}_samenvatting.docx"
```

**Wat doet het?**
- Orkestreert het hele proces
- Roept alle andere functies aan in de juiste volgorde
- `progress_callback` stuurt statusupdates naar de GUI
- Slaat bestanden op met timestamp in de naam

---

### 2. gui_app.py - De grafische interface

#### Tkinter basics

```python
import tkinter as tk

root = tk.Tk()                          # Maak hoofdvenster
root.title("YouTube Samenvatting")      # Zet titel
root.geometry("650x600")                # Zet afmetingen
```

**Tkinter widgets gebruikt:**
- `tk.Label` - Tekst labels
- `tk.Entry` - Tekst invoerveld
- `tk.Button` - Knoppen
- `tk.Radiobutton` - Keuze buttons
- `tk.Text` - Groot tekstveld
- `tk.LabelFrame` - Gegroepeerde sectie met titel
- `tk.Frame` - Container voor layout

#### Threading voor responsieve UI

```python
thread = threading.Thread(
    target=self.process_video_thread,
    args=(url, provider, api_key)
)
thread.daemon = True
thread.start()
```

**Waarom threading?**
- Zonder threading zou de UI "bevriezen" tijdens het verwerken
- De achtergrondthread doet het zware werk
- De UI blijft responsief
- `daemon=True` zorgt dat de thread stopt als de app sluit

#### Thread-safe UI updates

```python
def update_status(self, message):
    self.root.after(0, lambda: self.status_var.set(message))
```

**Waarom `root.after()`?**
- Tkinter is niet thread-safe
- Je mag de UI alleen updaten vanuit de hoofdthread
- `after(0, callback)` plant de callback in de hoofdthread

---

### 3. .env en environment variables

```python
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

api_key = os.environ.get("OPENAI_API_KEY", "")
```

**Hoe werkt het?**
1. `load_dotenv()` leest het `.env` bestand
2. Zet elke regel als environment variable
3. `os.environ.get()` haalt de waarde op
4. Het `.env` bestand staat in `.gitignore` voor veiligheid

---

### 4. De macOS .app bundle

De `.app` is eigenlijk een map met een specifieke structuur:

```
YouTube Samenvatting.app/
└── Contents/
    ├── Info.plist          # App metadata (naam, versie, etc.)
    ├── MacOS/
    │   └── launch          # Uitvoerbaar script
    └── Resources/          # (leeg, voor iconen etc.)
```

**launch script:**
```bash
#!/bin/bash
cd "/Users/jom/Documents/Kode/youtube-samenvatting"
source venv/bin/activate
exec python gui_app.py
```

---

## Dependencies (requirements.txt)

```
youtube-transcript-api>=0.6.0  # YouTube transcripties ophalen
openai>=1.0.0                  # OpenAI API client
anthropic>=0.18.0              # Anthropic API client
requests>=2.31.0               # HTTP requests (voor Ollama)
python-dotenv>=1.0.0           # Laden van .env bestanden
python-docx>=1.1.0             # Word documenten maken
pyinstaller>=6.0.0             # Voor bouwen van .app
```

---

## Prompt voor de samenvatting

De AI krijgt deze instructies:

```
Je bent een expert in het samenvatten van podcast en video content.
Maak een uitgebreide Nederlandse samenvatting van de volgende transcriptie.

Structuur je samenvatting als volgt:
## Hoofdonderwerp
[Korte beschrijving van waar de video over gaat]

## Belangrijkste punten
- [Punt 1]
- [Punt 2]
- [etc.]

## Gedetailleerde samenvatting
[Meer uitgebreide samenvatting van de inhoud]

## Conclusie/Takeaways
[De belangrijkste lessen of conclusies]
```

---

## Veelvoorkomende problemen

### "No module named '_tkinter'"
```bash
brew install python-tk@3.13
# Daarna venv opnieuw aanmaken
```

### "Kan geen verbinding maken met Ollama"
```bash
# Start Ollama eerst
ollama serve
```

### "API key is vereist"
Controleer of je `.env` bestand correct is ingevuld.

### Foutmeldingen debuggen
De app schrijft errors naar een logbestand:
```
~/.youtube_samenvatting.log
```
Bekijk dit bestand voor gedetailleerde foutmeldingen als iets niet werkt.

---

## Aanpassen en uitbreiden

### Ander OpenAI model gebruiken
In `youtube_samenvatting.py`, wijzig:
```python
model="gpt-4o-mini"  # Naar bijv. "gpt-4o" of "gpt-4-turbo"
```

### Ander Ollama model gebruiken
```python
model="gpt-oss:20b"  # Naar bijv. "llama3:8b" of "mistral:7b"
```

### Andere output map
```python
OUTPUT_DIR = Path.home() / "Documents" / "YouTube-Samenvattingen"
# Wijzig naar gewenste locatie
```

### Prompt aanpassen
Zoek naar de `prompt = """..."""` strings in de `summarize_with_*` functies.

---

## Licentie

Dit project is gemaakt voor persoonlijk gebruik.

---

*Gemaakt met hulp van Claude Code op 29 december 2024 - 31 december 2024*
