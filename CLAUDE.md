# YouTube Samenvatting

macOS desktop app die samenvattingen maakt van YouTube video's via transcripties en AI.

## Tech Stack

- **GUI**: tkinter
- **Transcripties**: youtube-transcript-api
- **AI**: OpenAI, Anthropic, of Ollama (lokaal)
- **Output**: python-docx (Word documenten)

## Starten

```bash
# Via terminal
source venv/bin/activate && python gui_app.py

# Of via desktop app
open ~/Desktop/YouTube\ Samenvatting.app
```

## Projectstructuur

```
youtube_samenvatting.py   # Hoofdmodule met alle logica
gui_app.py                # Grafische interface (tkinter)
.env                      # API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)
create_macos_app.sh       # Script om .app bundle te maken
```

## Belangrijke functies

- `extract_video_id(url)` - Haalt video ID uit YouTube URL
- `get_transcript(video_id)` - Haalt transcriptie op (Nederlands > Engels)
- `summarize_with_*()` - Samenvattingen via OpenAI/Anthropic/Ollama
- `process_video()` - Orkestreert het hele proces

## Output

Bestanden komen in `~/Documents/YouTube-Samenvattingen/`:
- `YYYYMMDD_HHMMSS_Titel_transcriptie.txt`
- `YYYYMMDD_HHMMSS_Titel_samenvatting.docx`

## Conventies

- Nederlandse samenvattingen
- Threading voor responsieve UI
- API keys in .env (nooit committen)
- Chat functie baseert antwoorden alleen op transcript
