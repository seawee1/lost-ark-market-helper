import pyautogui
import pytesseract
import cv2
from time import sleep
import numpy as np
from typing import NamedTuple
import itertools
from pytesseract import Output
import yaml

class Item(NamedTuple):
    type: str  # [Necklace, Ring, Earrings, Stone] supported for now
    name: str
    tier: str
    rank: str
    bonus_effects: dict
    engravings: dict


class Config:
    TESSERACT_BIN = "C:\Program Files\Tesseract-OCR\\tesseract.exe"
    LAYOUT_CONFIG_PATH = "layout_config.yaml"
    SCROLL_SPEED = 0.001
    SCROLL_STEPS = 1
    SLEEP_AFTER_HOVER = 0.2
    MOVE_TO_SPEED = 0.1


ITEM_RANKS = ["Overall", "Normal", "Uncommon", "Rare", "Epic", "Legendary", "Relic"]
ITEM_TIERS = ["All", "Tier 1", "Tier 2", "Tier 3"]
ITEM_CATEGORIES = [x.strip() for x in open("assets/category-menu-list.txt", "r").readlines()]
ITEM_COMBAT_STATS = [x.strip() for x in open("assets/combat-stats-menu-list.txt", "r").readlines()]
ITEM_ENGRAVINGS = [x.strip() for x in open("assets/engraving-menu-list.txt", "r").readlines()]
ACCESSORY_CATEGORIES = ["Necklace", "Earrings", "Ring"]
OTHER_ADVANCED_OPTIONS = ["All", "Combat Stats", "Engraving Effect"]


def click_event(event, x, y, flags, params):
    global click_event_return
    if event == cv2.EVENT_LBUTTONDOWN:
        click_event_return.append(np.array([x, y]))


def screenshot_cv():
    img = pyautogui.screenshot()
    cv_img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return cv_img


def click_on_screenshot(img, alert_msg=""):
    cv2.imshow('Screenshot', img)
    cv2.setMouseCallback('Screenshot', click_event)
    pyautogui.alert(alert_msg)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def parse_item_window(item_ocr_lst):
    if "Inventory" in item_ocr_lst:
        del (item_ocr_lst[item_ocr_lst.index("Inventory")])

    item_ocr_str = ' '.join(item_ocr_lst)

    item_name = None
    item_rank = None
    item_type = None
    item_bonus_effects = None
    item_engravings = None
    item_tier = None

    # Name and rank
    for rank in ITEM_RANKS:
        if rank.lower() in item_ocr_str.lower():
            item_rank = rank
            idx = item_ocr_str.lower().index(rank.lower())
            item_name = item_ocr_str[:idx].strip()
            # Converts e.g. "Fallen Blabla Necklace        y" into "Fallen Blabla Necklace"
            # item_name = item_name[:item_name.index("   ")]

    # Tier level
    tier_index = item_ocr_lst.index("Tier")
    item_tier = f"Tier {int(item_ocr_lst[tier_index + 1])}"

    # Identify type
    if "Necklace" in item_ocr_str:
        item_type = "Necklace"
    elif "Earrings" in item_ocr_str:
        item_type = "Earrings"
    elif "Ring" in item_ocr_str:
        item_type = "Ring"
    elif "Stone" in item_ocr_str:
        item_type = "Stone"
    else:
        return None  # raise NotImplementedError(f"{item_name} item type is not supported!")

    def extract_bonus_effects(item_ocr_str):
        bonus_effect_str = "Bonus Effect"
        bonus_effect_idx = item_ocr_str.lower().index(bonus_effect_str.lower())
        engraving_effect_str = "Random Engraving Effect"
        engraving_effect_idx = item_ocr_str.lower().index(engraving_effect_str.lower())

        bonus_effect_lst = item_ocr_str[bonus_effect_idx + len(bonus_effect_str): engraving_effect_idx].strip().split(
            " ")
        bonus_effects = dict()
        for i, strr in enumerate(bonus_effect_lst):
            if strr in ITEM_COMBAT_STATS:
                bonus_effect_name = strr  # Drop '[' and ']' at end
                bonus_effect_value = None
                while True:
                    i += 1
                    import re
                    if bonus_effect_lst[i].startswith("+"):
                        bonus_effect_value = int(re.sub(r'[^\w]', '', bonus_effect_lst[i]))
                        break

                bonus_effects[bonus_effect_name] = bonus_effect_value
        return bonus_effects

    def extract_engravings(item_ocr_str):
        bonus_effect_str = "Bonus Effect"
        engraving_effect_str = "Random Engraving Effect"
        engraving_effect_idx = item_ocr_str.lower().index(engraving_effect_str.lower())

        # Engravings
        engravings_substring = item_ocr_str[engraving_effect_idx + len(engraving_effect_str):].strip()
        engraving_effect_lst = list(itertools.chain(*[x.split("[") for x in engravings_substring.split("]")]))
        engraving_effect_lst = [x.strip() for x in engraving_effect_lst]

        engravings = {}
        for i, strr in enumerate(engraving_effect_lst):
            if strr in ITEM_ENGRAVINGS:
                engraving_name = strr
                engraving_value = None
                next_node_str = None
                while True:
                    i += 1
                    if "Node" in engraving_effect_lst[i]:
                        next_node_str = engraving_effect_lst[i]
                        break
                for x in next_node_str.split(" "):
                    if x.startswith("+"):
                        engraving_value = int(x)
                engravings[engraving_name] = engraving_value
        return engravings

    item_engravings = extract_engravings(item_ocr_str)
    if item_type != "Stone":
        item_bonus_effects = extract_bonus_effects(item_ocr_str)

    assert item_engravings is not None
    assert item_name is not None
    assert item_type is not None
    assert item_rank is not None
    if item_type != "Stone":
        assert item_bonus_effects is not None

    parsed_item = Item(item_type, item_name, item_tier, item_rank, item_bonus_effects, item_engravings)
    return parsed_item


def pick_from_dropdown(dropdown_position, entry_to_choose, dropdown_entry_lst, dropdown_num):
    print(dropdown_position, entry_to_choose)
    # How often do we need to scroll (num_scrolls)
    index = dropdown_entry_lst.index(entry_to_choose)
    num_scrolls = 0
    if index >= dropdown_num:
        num_scrolls = index - dropdown_num + 1

    # Where do we have to put our mouse (pos + offset + step * entry_steps in vertical direction)
    entry_steps = dropdown_entry_lst[num_scrolls:num_scrolls + dropdown_num].index(entry_to_choose)

    # Perform the movements and clicks
    # 1) Move to dropdown rectangle and open
    pyautogui.moveTo(*dropdown_position, Config.MOVE_TO_SPEED)
    pyautogui.click()

    # 2) Move to first element inside dropdown menu
    first_position = [
        dropdown_position[0],
        dropdown_position[1] + dropdown_offset]
    pyautogui.moveTo(*first_position, Config.MOVE_TO_SPEED)

    # 3) Do the required number of scrolls
    for _ in range(num_scrolls // Config.SCROLL_STEPS):
        pyautogui.scroll(-Config.SCROLL_STEPS)
        sleep(Config.SCROLL_SPEED)
    num_scrolls_mod = num_scrolls % Config.SCROLL_STEPS
    if num_scrolls_mod != 0:
        pyautogui.scroll(-num_scrolls_mod)

    # 4) Move to the entry inside dropdown we want to choose and click
    target_position = [
        first_position[0],
        first_position[1] + dropdown_step * entry_steps]
    pyautogui.moveTo(*target_position, Config.MOVE_TO_SPEED)
    pyautogui.click()


def extract_item_ocr_lst(position):
    # Move mouse over item
    pyautogui.moveTo(*position, Config.MOVE_TO_SPEED)
    sleep(Config.SLEEP_AFTER_HOVER)

    # Take a screenshot
    screenshot = screenshot_cv()

    # Take screenshot, cut and OCR
    screenshot = screenshot_cv()
    start_y = cell_pos[0] + window_offset
    end_y = start_y + window_width
    screenshot = screenshot[:, start_y:end_y, :]

    # OCR
    item_ocr = pytesseract.image_to_data(screenshot, output_type=Output.DICT)
    item_ocr_lst = item_ocr["text"]
    return item_ocr_lst


if __name__ == "__main__":
    click_event_return = []
    layout_config = None
    dropdown_offset = None
    dropdown_step = None

    # Set Tesseract path
    pytesseract.pytesseract.tesseract_cmd = Config.TESSERACT_BIN

    # Let's start
    pyautogui.alert("Bring Lost Ark to foreground. Press [OK] button afterwards.")
    sleep(0.5)

    # Get game resolution
    screen_width, screen_height = pyautogui.size()
    print(f"Detected {screen_width}x{screen_height} resolution...")

    # Load Config
    print(f"Loading layout configuration from {Config.LAYOUT_CONFIG_PATH}...")
    with open(Config.LAYOUT_CONFIG_PATH, "r") as f:
        try:
            layout_config = yaml.safe_load(f)
        except yaml.YAMLError as exc:
            print(exc)
    if f"{screen_width}x{screen_height}" in layout_config.keys():
        print("Success!")
        layout_config = layout_config[f"{screen_width}x{screen_height}"]
    else:
        raise Exception("Could not find valid configuration for your game resolution...")
    dropdown_offset = layout_config["advanced-search-window"]["dropdown"]["offset"]
    dropdown_step = layout_config["advanced-search-window"]["dropdown"]["step"]

    pyautogui.alert("Open your inventory and move it to the top-left corner.\n"
                    "Open the Market window.\n"
                    "Press [OK] button afterwards.")
    sleep(0.5)

    # Input inventory range to check
    range_str = pyautogui.prompt("Input 'start_row, start_col, end_row, end_col'. Each entry has to lie in [0, 9].")
    range_str = [int(x) for x in range_str.split(" ")]
    start_row, start_col, end_row, end_col = range_str
    print(f"Going from ({start_row}, {start_col}) up to ({end_row}, {end_col})...")

    # Extract items via mouse hover -> Screenshot and cut -> OCR -> Item NamedTuple
    items = []
    base_cell_pos = layout_config['inventory-window']['cell00-center']
    window_offset = layout_config['item-window']['offset-from-cell-center']
    window_width = layout_config['item-window']['width']
    for row in range(start_row, end_row + 1):
        for col in range(
                start_col if row == start_row else 0,
                end_col + 1 if row == end_row else 10):
            # Hover over item
            cell_pos = [
                base_cell_pos[0] + col * layout_config['inventory-window']['cell-size'],
                base_cell_pos[1] + row * layout_config['inventory-window']['cell-size']
            ]

            # Screenshot and OCR
            item_ocr_lst = extract_item_ocr_lst(cell_pos)

            # OCR to item NamedTuple
            item = parse_item_window(item_ocr_lst)
            if item is None:
                print(f"Oh oh! Could not parse ({row}, {col})!")
                continue

            items.append(item)

    for item in items:
        # Open Auction House tab
        pyautogui.moveTo(*layout_config["market-window"]["auction-house-button"], Config.MOVE_TO_SPEED)
        pyautogui.click()

        # Open Advanced Search window
        pyautogui.moveTo(*layout_config["market-window"]["advanced-open-button"], Config.MOVE_TO_SPEED)
        pyautogui.click()

        # Reset
        pyautogui.moveTo(*layout_config["advanced-search-window"]["default-button"], Config.MOVE_TO_SPEED)
        pyautogui.click()

        # Set category
        pick_from_dropdown(
            layout_config["advanced-search-window"]["category-button"],
            item.type,
            ITEM_CATEGORIES,
            layout_config["advanced-search-window"]["dropdown"]["category-num"]
        )

        # Set Class to 'All'
        pyautogui.moveTo(*layout_config["advanced-search-window"]["class-button"], Config.MOVE_TO_SPEED)
        pyautogui.click()

        base_position = [
            layout_config["advanced-search-window"]["class-button"][0],
            layout_config["advanced-search-window"]["class-button"][1] + dropdown_offset]
        pyautogui.moveTo(*base_position, Config.MOVE_TO_SPEED)
        for _ in range(5):
            pyautogui.scroll(3)
            sleep(Config.SCROLL_SPEED)
        pyautogui.click()

        # Set item rank
        pick_from_dropdown(
            layout_config["advanced-search-window"]["item-rank-button"],
            item.rank,
            ITEM_RANKS,
            layout_config["advanced-search-window"]["dropdown"]["rank-num"]
        )

        # Set item Tier
        pick_from_dropdown(
            layout_config["advanced-search-window"]["item-tier-button"],
            item.tier,
            ITEM_TIERS,
            layout_config["advanced-search-window"]["dropdown"]["tier-num"]
        )

        # Set Engravings
        for i, (name, value) in enumerate(item.engravings.items()):
            if i == 0:
                type_button = layout_config["advanced-search-window"]["other-advanced-options"]["first-type-button"]
                detail_button = layout_config["advanced-search-window"]["other-advanced-options"]["first-detail-button"]
            elif i == 1:
                type_button = layout_config["advanced-search-window"]["other-advanced-options"]["second-type-button"]
                detail_button = layout_config["advanced-search-window"]["other-advanced-options"][
                    "second-detail-button"]
            elif i == 2:  # This can happen, if we are looking at a ability stone
                type_button = layout_config["advanced-search-window"]["other-advanced-options"]["third-type-button"]
                detail_button = layout_config["advanced-search-window"]["other-advanced-options"]["third-detail-button"]

            # Set to "Engraving Effects"
            pick_from_dropdown(
                type_button,
                "Engraving Effect",
                OTHER_ADVANCED_OPTIONS,
                layout_config["advanced-search-window"]["dropdown"]["type-num"]
            )

            # Pick engraving
            pick_from_dropdown(
                detail_button,
                name,
                ITEM_ENGRAVINGS,
                layout_config["advanced-search-window"]["dropdown"]["detail-num"]
            )

        if item.type != "Stone":
            # Set bonus effects
            for i, (name, value) in enumerate(item.bonus_effects.items()):
                if i == 0:
                    type_button = layout_config["advanced-search-window"]["other-advanced-options"]["third-type-button"]
                    detail_button = layout_config["advanced-search-window"]["other-advanced-options"][
                        "third-detail-button"]
                elif i == 1:
                    type_button = layout_config["advanced-search-window"]["other-advanced-options"][
                        "fourth-type-button"]
                    detail_button = layout_config["advanced-search-window"]["other-advanced-options"][
                        "fourth-detail-button"]

                # Set to "Engraving Effects"
                pick_from_dropdown(
                    type_button,
                    "Combat Stats",
                    OTHER_ADVANCED_OPTIONS,
                    layout_config["advanced-search-window"]["dropdown"]["type-num"]
                )

                # Pick engraving
                pick_from_dropdown(
                    detail_button,
                    name,
                    ITEM_COMBAT_STATS,
                    layout_config["advanced-search-window"]["dropdown"]["detail-num"]
                )

        pyautogui.moveTo(*layout_config["advanced-search-window"]["search-button"], Config.MOVE_TO_SPEED)
        pyautogui.click()

        pyautogui.alert("Press [OK] to continue...")
