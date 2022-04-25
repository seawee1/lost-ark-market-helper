import pyautogui
import pytesseract
from time import sleep
from typing import NamedTuple
import itertools
from pytesseract import Output
import yaml
from util import screenshot_cv, read_adjusted_layout
import argparse

# Some layout constants
ITEM_RANKS = [x.strip() for x in open("res/layout/dropdowns/category.txt", "r").readlines()]
ITEM_TIERS = [x.strip() for x in open("res/layout/dropdowns/item-tier.txt", "r").readlines()]
ITEM_CATEGORIES = [x.strip() for x in open("res/layout/dropdowns/category.txt", "r").readlines()]
ITEM_COMBAT_STATS = [x.strip() for x in open("res/layout/dropdowns/combat-stats.txt", "r").readlines()]
ITEM_ENGRAVINGS = [x.strip() for x in open("res/layout/dropdowns/engravings.txt", "r").readlines()]
OTHER_ADVANCED_OPTIONS = [x.strip() for x in open("res/layout/dropdowns/other-advanced-options.txt", "r").readlines()]


class Item(NamedTuple):
    type: str
    name: str
    tier: str
    rank: str
    bonus_effects: dict
    engravings: dict


def extract_item_ocr_lst(position):
    # Move mouse over item
    pyautogui.moveTo(*position, args.move_to_speed)
    sleep(args.sleep_after_hover)

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


def parse_item_ocr_lst(item_ocr_lst):
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
    pyautogui.moveTo(*dropdown_position, args)
    pyautogui.click()

    # 2) Move to first element inside dropdown menu
    first_position = [
        dropdown_position[0],
        dropdown_position[1] + dropdown_offset]
    pyautogui.moveTo(*first_position, args.move_to_speed)

    # 3) Do the required number of scrolls
    for _ in range(num_scrolls):
        pyautogui.scroll(-1)
        sleep(args.scroll_speed)

    # 4) Move to the entry inside dropdown we want to choose and click
    target_position = [
        first_position[0],
        first_position[1] + dropdown_step * entry_steps]
    pyautogui.moveTo(*target_position, args.move_to_speed)
    pyautogui.click()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--tesseract-bin-path', type=str, default="C:\Program Files\Tesseract-OCR\tesseract.exe")
    parser.add_argument('--layout-config-path', type=str, default="res\layout\layout-info.yaml")
    parser.add_argument('--scroll-speed', type=float, default=0.01)
    parser.add_argument('--sleep-after-hover', type=float, default=0.2)
    parser.add_argument('--move-to-speed', type=float, default=0.1)
    parser.add_argument('--manually-advanced', action='store_true')
    parser.add_argument('--scan-inventory', action='store_true')
    args = parser.parse_args()

    # See assertion message
    if args.manually_advanced:
        assert args.scan_inventory is True, "In order to manually enter item stats into the advanced item search " \
                                            "form, the item gear stats have to be extracted via OCR. Passing the " \
                                            "'--scan-inventory' flag will activate this behavior. "

    # Set Tesseract path
    pytesseract.pytesseract.tesseract_cmd = args.tesseract_bin_path

    # Let's start
    pyautogui.alert("Bring Lost Ark to foreground. Press [OK] button afterwards.")
    sleep(0.5)

    # Get game resolution
    screen_width, screen_height = pyautogui.size()
    res_str = f"{screen_width}x{screen_height}"
    print(f"Detecting {screen_width}x{screen_height} screen resolution...")

    # Load layout description, automatically adjust to current game resolution
    print(f"Loading layout description from {args.layout_config_path}...")
    layout = read_adjusted_layout(res_str, args.layout_config_path)
    dropdown_offset = layout["advanced-search-window"]["dropdown"]["offset"]
    dropdown_step = layout["advanced-search-window"]["dropdown"]["step"]

    pyautogui.alert("Open your inventory and move it to the top-left corner.\n"
                    "Open the Market window.\n"
                    "Press [OK] button afterwards.")
    sleep(0.5)

    # Input inventory range to check
    range_str = pyautogui.prompt("Input 'end_row end_col'. Starts at (0, 0), row-first, column-last. Indexing from "
                                 "[0, 9]. End indices are inclusive.")
    range_str = [int(x) for x in range_str.split(" ")]
    start_row, start_col, end_row, end_col = range_str
    print(f"Going from ({start_row}, {start_col}) to ({end_row}, {end_col})...")

    # Extract items via mouse hover -> Screenshot and cut -> OCR -> Item NamedTuple
    items = []
    rows_cols = []
    base_cell_pos = layout['inventory-window']['upper-left-cell']
    window_offset = layout['item-window']['offset-from-cell-center']
    window_width = layout['item-window']['width']
    for row in range(start_row, end_row + 1):
        for col in range(
                start_col if row == start_row else 0,
                end_col + 1 if row == end_row else 10):
            rows_cols.append((row, col))

            if not args.scan_inventory:
                continue

            # Hover over item
            cell_pos = [
                base_cell_pos[0] + col * layout['inventory-window']['cell-size'],
                base_cell_pos[1] + row * layout['inventory-window']['cell-size']
            ]
            # Screenshot and OCR
            item_ocr_lst = extract_item_ocr_lst(cell_pos)

            # OCR to item NamedTuple
            item = parse_item_ocr_lst(item_ocr_lst)
            if item is None:
                print(f"Oh oh! Could not parse ({row}, {col})!")
                continue

            items.append(item)

    if args.scan_inventory:
        print("===================== Detected Gear =====================")
        for i, (row, col) in enumerate(rows_cols):
            print(f"({row}, {col}) | {items[i]}")
        print("=========================================================")

    if args.manually_advanced:
        # We let our bot enter the detected item stats manually into the advanced search window
        for i, (row, col) in enumerate(rows_cols):
            item = items[i]

            # Open Auction House tab
            pyautogui.moveTo(*layout["market-window"]["auction-house-button"], args.move_to_speed)
            pyautogui.click()

            # Open Advanced Search window
            pyautogui.moveTo(*layout["market-window"]["advanced-open-button"], args.move_to_speed)
            pyautogui.click()

            # Reset
            pyautogui.moveTo(*layout["advanced-search-window"]["default-button"], args.move_to_speed)
            pyautogui.click()

            # Set category
            pick_from_dropdown(
                layout["advanced-search-window"]["category-button"],
                item.type,
                ITEM_CATEGORIES,
                layout["advanced-search-window"]["dropdown"]["category-num"]
            )

            # Set Class to 'All'
            pyautogui.moveTo(*layout["advanced-search-window"]["class-button"], args.move_to_speed)
            pyautogui.click()

            base_position = [
                layout["advanced-search-window"]["class-button"][0],
                layout["advanced-search-window"]["class-button"][1] + dropdown_offset]
            pyautogui.moveTo(*base_position, args.move_to_speed)
            for _ in range(10):
                pyautogui.scroll(1)
                sleep(args.scroll_speed)
            pyautogui.click()

            # Set item rank
            pick_from_dropdown(
                layout["advanced-search-window"]["item-rank-button"],
                item.rank,
                ITEM_RANKS,
                layout["advanced-search-window"]["dropdown"]["rank-num"]
            )

            # Set item tier
            pick_from_dropdown(
                layout["advanced-search-window"]["item-tier-button"],
                item.tier,
                ITEM_TIERS,
                layout["advanced-search-window"]["dropdown"]["tier-num"]
            )

            # Set Engravings
            for i, (name, value) in enumerate(item.engravings.items()):
                # TODO: There's a bug with the indexing. Items with e.g. 1 bonus effect and 3 engravings are not entered correctly.
                if i == 0:
                    type_button = layout["advanced-search-window"]["other-advanced-options"]["first-type-button"]
                    detail_button = layout["advanced-search-window"]["other-advanced-options"]["first-detail-button"]
                elif i == 1:
                    type_button = layout["advanced-search-window"]["other-advanced-options"]["second-type-button"]
                    detail_button = layout["advanced-search-window"]["other-advanced-options"][
                        "second-detail-button"]
                elif i == 2:  # This can happen, if we are looking at a ability stone
                    type_button = layout["advanced-search-window"]["other-advanced-options"]["third-type-button"]
                    detail_button = layout["advanced-search-window"]["other-advanced-options"]["third-detail-button"]

                # Set to "Engraving Effects"
                pick_from_dropdown(
                    type_button,
                    "Engraving Effect",
                    OTHER_ADVANCED_OPTIONS,
                    layout["advanced-search-window"]["dropdown"]["type-num"]
                )

                # Pick engraving
                pick_from_dropdown(
                    detail_button,
                    name,
                    ITEM_ENGRAVINGS,
                    layout["advanced-search-window"]["dropdown"]["detail-num"]
                )

            if item.type != "Stone":
                # Set bonus effects
                for i, (name, value) in enumerate(item.bonus_effects.items()):
                    if i == 0:
                        type_button = layout["advanced-search-window"]["other-advanced-options"]["third-type-button"]
                        detail_button = layout["advanced-search-window"]["other-advanced-options"][
                            "third-detail-button"]
                    elif i == 1:
                        type_button = layout["advanced-search-window"]["other-advanced-options"][
                            "fourth-type-button"]
                        detail_button = layout["advanced-search-window"]["other-advanced-options"][
                            "fourth-detail-button"]

                    # Set to "Engraving Effects"
                    pick_from_dropdown(
                        type_button,
                        "Combat Stats",
                        OTHER_ADVANCED_OPTIONS,
                        layout["advanced-search-window"]["dropdown"]["type-num"]
                    )

                    # Pick engraving
                    pick_from_dropdown(
                        detail_button,
                        name,
                        ITEM_COMBAT_STATS,
                        layout["advanced-search-window"]["dropdown"]["detail-num"]
                    )

            pyautogui.moveTo(*layout["advanced-search-window"]["search-button"], args.move_to_speed)
            pyautogui.click()

            pyautogui.alert("Press [OK] to continue...")
    else:
        # Hover over item
        for i, (row, col) in enumerate(rows_cols):
            # Open Auction House tab
            pyautogui.moveTo(*layout["market-window"]["auction-house-button"], args.move_to_speed)
            pyautogui.click()

            # Hover over item
            cell_pos = [
                base_cell_pos[0] + col * layout['inventory-window']['cell-size'],
                base_cell_pos[1] + row * layout['inventory-window']['cell-size']
            ]
            pyautogui.moveTo(*cell_pos, args.move_to_speed)

            # CTRL+RMB -> "Check Market Value" option
            pyautogui.keyDown('ctrl')
            pyautogui.rightClick()
            pyautogui.keyUp('ctrl')
            market_value_button = [
                cell_pos[0] + 188 - 138,
                cell_pos[1] + 215 - 111  # TODO: to layout-info.yaml
            ]
            sleep(0.2)
            pyautogui.moveTo(*market_value_button, args.move_to_speed)
            pyautogui.click()
            sleep(0.2)

            # Click Advanced Search
            pyautogui.moveTo(*layout['market-window']['advanced-open-button'], args.move_to_speed)
            pyautogui.click()
            sleep(0.2)

            # Remove item name
            # TODO: to layout-info.yaml
            pyautogui.moveTo(*[2022, 365], args.move_to_speed)
            pyautogui.click()

            # Click search
            pyautogui.moveTo(*layout["advanced-search-window"]["search-button"], args.move_to_speed)
            pyautogui.click()
            sleep(0.2)

            # Click on Search tab
            # TODO: to layout-info.yaml
            pyautogui.moveTo(*[923, 268], args.move_to_speed)
            pyautogui.click()

            # TODO: input mask -> automatic auction, dismantle or keep

            pyautogui.alert("Press [OK] to continue...")