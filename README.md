\# Auto-Clip \& Caption Studio



A free, local, watermark-free vertical video clipper and word-by-word caption generator built with Python, `faster-whisper`, FFmpeg, and Flask.



\## Features

\- \*\*Local Speech-to-Text:\*\* Uses `faster-whisper` (`base.en`, `int8`) to generate word-level timestamps locally with zero paid API keys.

\- \*\*9:16 Vertical Cropping:\*\* Automatically crops horizontal video to `1080x1920` for Shorts, Reels, and TikTok.

\- \*\*Active Word Captions:\*\* Burns bold, high-contrast captions with active word highlighting via FFmpeg and `.ass` subtitles.

\- \*\*Browser Dashboard + Ad Slots:\*\* Includes a local Flask web UI (`http://127.0.0.1:5000`) with configurable ad slots for free ad-supported distribution.



\## Prerequisites

\- \*\*Python 3.11+\*\*

\- \*\*FFmpeg\*\* installed and added to your system `PATH`



\## Setup \& Usage



1\. Install Python dependencies:

&#x20;  ```bash

&#x20;  pip install faster-whisper flask





python clipper.py test.mp4 30

python app.py







