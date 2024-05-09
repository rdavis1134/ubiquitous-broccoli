from time import sleep
from datetime import datetime
import pytz
import pyautogui

import datalink


def find_image(img, conf=0.9, stop=0.86, area=None):
    # Search for a specified image. Suppresses the Exception when/if it isn't found.
    # Instead of crashing, it waits a moment then decreases the confidence by 0.01 and tries again.
    # Returns the location of the image (left, top, width, height) if found.
    # Returns None if the image isn't found by/before confidence 0.8.
    while True:
        try:
            return pyautogui.locateOnScreen(img, confidence=conf, region=area)
        except pyautogui.ImageNotFoundException as err:
            conf -= 0.01
        if conf < stop:
            break
    return None


def back_out(back_pos=None, game_region=None):
    if not back_pos:
        back_btn = find_image(r"images\Navigation_back1.png", area=game_region)
        back_pos = pyautogui.center(back_btn)
    pyautogui.click(back_pos)
    sleep(0.3)


def build_buy_buttons(threshold: int = 3, game_region=None):
    # Without OCR (not presently available in pyautogui), there isn't enough difference between the
    # buy buttons to accurately detect each one uniquely. Instead, we'll find the add buttons, then
    # find the buy button associated with each one by color.
    # game_region:      Where we already expect the game to be on-screen, if available.
    # Returns dictionary of click locations labeled for the add buttons and corresponding buy buttons.

    click_locs = {}
    # Build the list of add buttons.
    add_btns = []
    already_found = []
    for add_btn in pyautogui.locateAllOnScreen(r"images\Events_add.png", confidence=0.86, region=game_region):
        add_pos = pyautogui.center(add_btn)
        if add_pos in already_found:
            continue
        add_btns.append(add_btn)
        for i in range(-1*threshold, threshold+1):
            for j in range(-1*threshold, threshold+1):
                already_found.append((add_pos[0]+i, add_pos[1]+j))
    # There should only be four add buttons (unless they update the game eventually).
    if len(add_btns) > 4:
        return build_buy_buttons(threshold+1, game_region)
    if (threshold > 10) and (len(add_btns) != 4):
        return None     # Something has gone wrong, probably the Event expired or they updated something big.
    # Sort the add button list and build the button dictionary.
    keylist = ["itemfree_{}", "item20_{}", "item50_{}", "item100_{}"]
    ordered_btns = sorted(add_btns, key=lambda btn: btn[1])
    for ix, btn in enumerate(ordered_btns):
        add_pos = pyautogui.center(btn)
        click_locs[keylist[ix].format("add")] = add_pos
        buy_area = (btn[0] + btn[2]//2, btn[1] - 2*btn[3], 3*btn[2], 3*btn[3])
        buy_btn = find_image(r"images\Events_buy.png", area=buy_area)
        if buy_btn:
            buy_pos = pyautogui.center(buy_btn)
        else:   # We couldn't find the buy button, so make an educated guess.
            buy_pos = (add_pos[0] + 3*btn[2]//2, add_pos[1] - btn[3])
        click_locs[keylist[ix].format("buy")] = buy_pos
    return click_locs


def buy_items(buy_amounts, game_region=None):
    # Buy the appropriate Event items.
    # buy_amounts:      The sub-dictionary that specifies how many of each item to buy for this Event.
    # game_region:      Where we already expect the game to be on-screen, if available.
    # Returns True if Event items were purchased, False if the Event has expired.

    cancel_btn = find_image(r"images\Events_cancel.png", area=game_region)
    if not cancel_btn:
        return False    # The item menu didn't open. The Event has expired.
    click_positions = build_buy_buttons(game_region=game_region)
    if not click_positions:
        return False    # Something went wrong, we can't do Events right now.
    for item in buy_amounts.keys():
        if buy_amounts[item] == 0:
            continue    # We don't want to buy any of this item.
        item_str = "{}_{}"
        for i in range(1, int(buy_amounts[item])):
            pyautogui.click(click_positions[item_str.format(item, "add")])
            sleep(0.2)
        pyautogui.click(click_positions[item_str.format(item, "buy")], clicks=2, interval=1.5)
        sleep(3)
    pyautogui.click(pyautogui.center(cancel_btn), clicks=4, interval=0.5)   # Sometimes doesn't detect it.
    return True


def use_items(back_pos=None, game_region=None):
    # Uses all available Event items.
    # back_pos:         Location of the back button, if already known.
    # game_region:      Where we already expect the game to be on-screen, if available.
    # Returns True if we clicked the Use button at least once, False otherwise.

    use_btn = find_image(r"images\Events_use.png", area=game_region)
    if not use_btn:
        return False    # There aren't any Event items to use.
    use_pos = pyautogui.center(use_btn)
    use_region = (use_btn[0] - use_btn[2]//2, use_btn[1] - use_btn[3]//2, 2*use_btn[2], 2*use_btn[3])
    # empty_region = (use_btn[0], use_btn[1] - 4*use_btn[3], use_btn[2], 5*use_btn[3])
    # empty_btn = find_image(r"images\Events_empty.png", area=empty_region)   # Initialize this first.
    usex10_region = (use_btn[0] + use_btn[2], use_btn[1], 2*use_btn[2], 3*use_btn[3])
    usex10_btn = find_image(r"images\Events_usex10.png", stop=0.8, area=usex10_region)
    if not back_pos:
        back_btn = find_image(r"images\Navigation_back2.png", area=game_region)
        back_pos = pyautogui.center(back_btn)
    if usex10_btn:
        pyautogui.click(pyautogui.center(usex10_btn))
    keep_looking = 10       # Lag is really trashing my ability to reliably detect the wretched buttons!
    while keep_looking:     # So instead, we'll force it to keep looking. Unbelievable this is necessary.
        pyautogui.click(use_pos)    # I guess the saving grace is that in doing so much more work, it can
        sleep(1)                    # adjust (slightly) to the timing differences between Events.
        use_btn = find_image(r"images\Events_use.png", area=use_region)
        if use_btn:
            keep_looking = 11
        keep_looking -= 1
    sleep(3)
    pyautogui.click(back_pos)
    return True


def main(try_anyway=False, back_pos=None, game_region=None):
    # Main entry point to the Events auto-clicker.
    # try_anyway:       Try to run Events even if the log says we already have today.
    # back_pos:         The position of the back button, if already known.
    # game_region:      Where we already expect the game to be on-screen, if available.

    # Check if we already bought and used event items today.
    already_complete = False
    today_jst = datetime.now(pytz.timezone('Asia/Tokyo'))
    today_jst_filename = r"data\{}.json".format(today_jst.strftime("%Y-%m-%d"))
    current = datalink.fetch_json(today_jst_filename)
    if (not try_anyway) and ("Events" in current.keys()):
        already_complete = current["Events"]["already_complete"]
    # Check which Events are currently running
    print("---\nStarting Events")
    if not already_complete:
        settings = datalink.fetch_json("settings.json")
        for key in settings["Events"].keys():
            if not settings["Events"][key]:
                continue    # This Event doesn't have a populated sub-dictionary, so don't do anything.
            img_str = r"images\Ops_{}.png".format(key)
            print("\tChecking for {}".format(key))
            event_btn = find_image(img_str, area=game_region)   # If it's here, it's recognized by 0.88->0.86
            if not event_btn:
                continue
            pyautogui.click(pyautogui.center(event_btn))
            sleep(0.5)
            items_btn = find_image(r"images\Events_items.png", area=game_region)
            pyautogui.click(pyautogui.center(items_btn))
            sleep(0.5)
            items_bought = buy_items(settings["Events"][key], game_region)
            if not items_bought:    # This Event has expired. Back out and keep looking.
                back_out(back_pos, game_region)
                continue
            join_btn = find_image(r"images\Events_{}join.png".format(key), area=game_region)
            if not join_btn:    # Possible fault in items_bought, misdetection of cancel_btn.
                back_out(back_pos, game_region)
                continue
            pyautogui.click(pyautogui.center(join_btn))
            sleep(0.5)
            items_used = use_items(back_pos, game_region)
            if items_used:
                current["Events"] = {"already_complete": True}
                sleep(3)    # Sometimes the menu-click timing handoff doesn't hold tight.
                back_out(back_pos, game_region)
    datalink.save_json(today_jst_filename, current)


if __name__ == "__main__":
    # Backup entry point to the Events auto-clicker, presumably from the command line.
    print("entered events.py")
    sleep(2)
    main(try_anyway=True, game_region=None)

