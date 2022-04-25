# Lost Ark Market Lookup
A "bot" that scans sellable gear items (Accessories + Ability Stones) inside your inventory using OCR and checks their price on the auction house.

## Setup
- Run ```pip install -r requirements.txt``` to install the required Python packages.
- Download and install [Tesseract](https://tesseract-ocr.github.io/tessdoc/Downloads.html). Adjust the Config.TESSERACT_BIN path inside ```main.py``` if necessary.

### UI Layout Configuration
The in-game UI layout definition is stored inside ```layout_config.yaml```. The current definition is only valid for a 3440x1440 display resolution (21:9).

Should your monitor have a different resolution you will have to provide a valid layout definition first. 
To do so, simply duplicate the definition inside the file, change the "widthxheight" field to your display resolution and adjusted the other field values to the correct values.

The following suggestions should work, but are untested:
- 2K resolution (2560x1440): Substract (3440 - 2560) / 2 = 440 from the first dimension of every coordinate entry except for *cell00-center*.
- 21:9 Full HD resolution (2560×1080): Multiply the coordinate and length values by 1080 / 1440 = 0.75.
- Standard Full HD (1920x1080): Perform both 1. and 2.
- Every other resolution: You will have to do the math by yourself, hehe.

Alternatively, you can capture similar screenshots as the ones inside ```assets/reference-images-21_9``` and manually read of the correct values (e.g. using Paint).

## Usage
Run ```python main.py``` to start the script. Just follow the instructions afterwards.

## Outlook
I might switch the workflow towards a summary print and/or make the script automatically create auctions for promising items.

There are also probably some bugs in there. Might or might not fix, we'll see.