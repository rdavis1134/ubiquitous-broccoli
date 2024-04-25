from time import sleep
from datetime import datetime
import pytz
import pyautogui
import pyscreeze

import datalink


def find_image(img, conf=0.9, area=None):
    # Search for a specified image. Suppresses the Exception when/if it isn't found.
    # Instead of crashing, it waits a moment then decreases the confidence by 0.01 and tries again.
    # Returns the location of the image (left, top, width, height) if found.
    # Returns None if the image isn't found by/before confidence 0.8.
    while True:
        try:
            return pyautogui.locateOnScreen(img, confidence=conf, region=area)
        except pyautogui.ImageNotFoundException as err:
            sleep(0.2)
            conf -= 0.01
        if conf < 0.8:
            break
    return None


def build_search_areas(game_region=None):
    # The image search is slow, so speed it up by reducing the search area.
    # The search area for just the icons is too small to include the Auto and Dispatch buttons,
    # so we'll also return a search area to find those as well.
    # game_region:      Where we already expect the game to be on-screen, if available.
    # Returns:          Tuple(useful search area, larger search area)

    back_btn = find_image(r"images\Navigation_back1.png", area=game_region)
    refresh_btn = find_image(r"images\CrewDispatch_refresh.png", area=game_region)
    search_left = back_btn[0]
    search_top = back_btn[1] + 2*back_btn[3]
    search_width = refresh_btn[0] + refresh_btn[2] - search_left
    search_height = refresh_btn[1] - search_top
    search_region = (search_left, search_top, search_width, search_height)
    extended_height = search_height + 2*refresh_btn[3]
    extended_region = (search_left, search_top, search_width, extended_height)
    return (search_region, extended_region)


def attempt_rounds(rounds: int, already_done: int, refresh_wait: int, images, search_area, extend_area):
    # Try to play the remaining rounds of Crew Dispatch.
    # rounds:           How many rounds are meant to be played.
    # already_done:     How many rounds have already been played.
    # refresh_wait:     How long to wait after each round before refreshing.
    # images            A List of the type images to search for.
    # search_area:      Where we expect items to be on-screen.
    # extend_area:      Where we expect the buttons to be.
    # Returns:          The number of rounds which have been completed in total.

    refresh_btn = find_image(r"images\CrewDispatch_refresh.png", area=extend_area)
    refresh_pos = pyautogui.center(refresh_btn)
    auto_btn = None
    auto_pos = None
    dispatch_btn = None
    dispatch_pos = None
    cancel_btn = None
    cancel_pos = None
    rnd = already_done
    print("---\nStarting Crew Dispatch")
    for rnd in range(already_done+1, rounds+1):
        print("\tround #{}".format(rnd))
        for img in images:
            keep_checking = 2   # For some reason, this garbage occasionally misses items.
            checked_locs = []   # Don't infinitely re-check items that couldn't be completed.
            while keep_checking:
                keep_checking -= 1
                add_if_found = True
                try:
                    for loc in pyautogui.locateAllOnScreen(img, confidence=0.85, region=search_area):
                        loc_pos = pyautogui.center(loc)
                        if loc_pos in checked_locs:
                            continue    # Who needs fancy tricks when I can just abuse lists?
                        pyautogui.click(loc_pos)
                        for i in range(-3, 4):      # Might be a good idea to check this eventually.
                            for j in range(-3, 4):  # Variability may be less than +- 3 pixels.
                                checked_locs.append((loc_pos[0]+i, loc_pos[1]+j))
                        if (not auto_btn) or (not dispatch_btn) or (not cancel_btn):
                            sleep(0.3)
                            auto_btn = find_image(r"images\CrewDispatch_auto.png", area=extend_area)
                            auto_pos = pyautogui.center(auto_btn)
                            dispatch_btn = find_image(r"images\CrewDispatch_dispatch.png", area=extend_area)
                            dispatch_pos = pyautogui.center(dispatch_btn)
                            cancel_btn = find_image(r"images\CrewDispatch_cancel1.png", area=extend_area)
                            cancel_pos = pyautogui.center(cancel_btn)
                        sleep(0.3)
                        pyautogui.click(auto_pos, clicks=2, interval=0.3)
                        pyautogui.click(dispatch_pos)
                        sleep(1.5)
                        pyautogui.click(cancel_pos)
                        sleep(0.3)
                        if add_if_found:
                            keep_checking += 1      # If we found something, check again just in case.
                            add_if_found = False    # But only check again one more time.
                except pyscreeze.ImageNotFoundException as err:
                    sleep(1)
                    continue
        if rnd != rounds:
            sleep(refresh_wait)
            pyautogui.click(refresh_pos)
            sleep(2)    # 1.5 seconds may not be fully enough time for the pulse animation to clear.
    return rnd


def main(game_region=None):
    # Main entry point to the Crew Dispatch auto-clicker.
    # game_region:     Where we already expect the game to be on-screen, if available.

    # Check if we have to do anything in the first place.
    settings = datalink.fetch_json("settings.json")
    try:
        rounds = int(settings["CrewDispatch"]["rounds"])
    except KeyError:    # If we're here, someone asked specifically for Crew Dispatch, either
        rounds = 1      # from app.py or the backdoor here. Allow a one round default.
    today_jst = datetime.now(pytz.timezone('Asia/Tokyo'))
    today_jst_filename = r"data\{}.json".format(today_jst.strftime("%Y-%m-%d"))
    current = datalink.fetch_json(today_jst_filename)
    if "CrewDispatch" not in current.keys():
        already_done = 0
    else:
        already_done = int(current["CrewDispatch"]["already_done"])
    if rounds > already_done:
        # Check to be certain we're actually in Crew Dispatch.
        label_loc = find_image(r"images\CrewDispatch_label.png", area=game_region)
        if not label_loc:
            raise ValueError("Not in the Crew Dispatch activity!")
        # Build search regions and validate the types we're looking for.
        search_area, extend_area = build_search_areas(game_region)
        images = []
        possibles = [("B_type", r"images\CrewDispatch_B.png"),
                     ("C_type", r"images\CrewDispatch_C.png"),
                     ("G_type", r"images\CrewDispatch_G.png"),
                     ("L_type", r"images\CrewDispatch_L.png"),
                     ("S_type", r"images\CrewDispatch_S.png")]
        for option in possibles:
            try:
                if settings["CrewDispatch"][option[0]]:
                    images.append(option[1])
            except KeyError:
                pass
        if "wait_before_refresh" in settings["CrewDispatch"].keys():
            refresh_wait = settings["CrewDispatch"]["wait_before_refresh"]
        else:
            refresh_wait = 2
        rounds_completed = attempt_rounds(rounds, already_done, refresh_wait, images, search_area, extend_area)
        current["CrewDispatch"] = {"already_done": rounds_completed}
        datalink.save_json(today_jst_filename, current)


if __name__ == "__main__":
    # Backup entry point to the Crew Dispatch auto-clicker, presumably from the command line.
    print("entered crewdispatch.py")
    sleep(2)
    main(None)

