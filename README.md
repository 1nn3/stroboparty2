# Stroboparty2 🎶🎉

**⚠️ WARNING**: This script simulates a strobe effect. Do not run if you are sensitive to flashing lights.

* **[Lichttherapie](https://de.wikipedia.org/wiki/Lichttherapie)**
* __[Farbtherapie](https://de.wikipedia.org/wiki/Farbtherapie)__
* `./hz-player.py -a dope # Rave approved`
* `./hz-player.py -a flowermix # Dancehall/Disco approved`
* `./hz-player.py -T -a <dots|dots2> # are you ready to music?`

## Install

First install Python:

	apt install python3-venv python-is-python3

Than install Stroboparty2:

	git clone https://github.com/1nn3/stroboparty2 ~/stroboparty2
	cd ~/stroboparty2
	python -m venv venv
	. venv/bin/activate
	python -m pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt
	python ./hz-player.py

Most modern Python installations (3.4+) include pip automatically. You can check with:

	python --version
	python -m pip --version

## FAQ

### How to Mux (with FFmpeg)

	ffmpeg [-ss HH:MM:SS] [-t HH:MM:SS] -vn -i <input> -f wav audio.wav
	./hz-player -i audio.wav -r record.avi
	ffmpeg [-ss HH:MM:SS] [-t HH:MM:SS] -i record.avi -i audio.wav -f mp4 video.mp4

### `OSError: PortAudio library not found` (Debian and Debian based)

	apt update && apt install libportaudio2 # or portaudio19-dev
	pip install --upgrade --force-reinstall -r requirements.txt

### `ModuleNotFoundError: No module named 'setuptools._distutils.msvccompiler'` (Microsoft Windows)

Install Microsoft Build Tools (needed for C extensions).

Pygame sometimes needs MSVC if it falls back to building from source. Install Microsoft C++ Build Tools (From Visual Studio Installer by selecting Desktop development with C++).

Alternative install Python 3.12 or 3.11. These versions have official Pygame wheels.

After installation run:

	pip install --upgrade --force-reinstall -r requirements.txt

### How to download music form YouTube

In short:

	apt --install-suggests install yt-dlp
	yt-dlp --cookies-from-browser firefox -x <https://www.youtube.com/…>

## Examples

### Examples for *none* strobes effects

Blue Theme:

	./start.sh --strobe-mode solid_b --colors blue_colors --effect konfetti --hint Blue

### Examples for *medium* strobes effects

	./start.sh --auto-mode come_in

Dancehall/Disco: 

	./start.sh --auto-mode triangle_colorstrobe

Or `start.sh --strobe-mode konfetti_colors --color-mode grayscale_colors --effect triangle --hint Dancehall`

Rave: 

	./start.sh --auto-mode dope

Or `start.sh --strobe-mode bw_colors --color-mode bw_colors --effect lametta --hint Rave`

## Sonstiges

* [radio.garden](https://radio.garden)

