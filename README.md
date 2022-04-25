# Lost Ark Gear-to-Money Auction Helper
A little quality of life tool that mashes some buttons for you to comfortably look up the market values of those juicy gear pieces occupying half of your inventory space. 

Because cycling through *Item menu -> Check Market Value -> Clear name field -> Search button -> Search tab* is boring as hell, we outsource this task to our little *computing slav...* eeeeh... *friend!*


## Setup
Setup the Python environment via ```pip install -r requirements.txt```.

## Usage

Run ```python main.py``` to start the tool. Afterwards, just follow the appearing instruction windows.

*Pro-tip:* The gear items under investigation are best placed at the beginning of your inventory storage.

### UI Layout Description
The layout description required to interact with the LOA user interface is contained inside the ```res/layout-info.yaml``` file.
The coordinates and pixel offsets correspond to a game running at 3440x1440 render resolution. 
In theory, the ```read_adjusted_layout``` method inside ```utils.py``` implements automatic rescale and shifting of these values in order to fit to your screen resolution. 
In practice however, the code is yet untested, so don't be surprised if it does not work right out-of-the-box.

### Extra Functionalities
- Passing ```--scan-inventory``` will enable item scanning. At the beginning, the tool will go successively over every of the specified inventory cells and extract item attributes via an OCR approach, including item name, rarity, tier, engraving effects, and more. 
This requires [Tesseract](https://github.com/tesseract-ocr/tesseract) to be downloaded and installed. 
Should the executable path differ from the default path on Windows, you will have to pass the correct path using ```--tesseract-bin-path /path/to/tesseract```.

- When running the tool with the ```--manual-advanced``` flag, item attributes will be entered manually into the advanced item search form via mouse inputs. 
The function is quite useless, but respective code portions might be recyclable for future ideas.

## Outlook
As of right now the script just goes through your inventory slots and loops through a button pressing routine.
As a next step, it would be cool if one could tell the tool what to do with an item once we know its rough value in gold, e.g. put the item up for auction, throw it in the trash or hodl it.