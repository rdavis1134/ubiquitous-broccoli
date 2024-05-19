from time import sleep
from datetime import datetime
import pytz
import pyautogui

import datalink


def find_image(img, conf=0.9, area=None):
    # Search for a specified image. Suppresses the Exception when/if it isn't found.
    # Instead of crashing, it waits a moment then decreases the confidence by 0.01 and tries again.
    # Returns the location of the image (left, top, width, height) if found.
    # Returns None if the image isn't found by/before confidence 0.88.
    while True:
        try:
            return pyautogui.locateOnScreen(img, confidence=conf, region=area)
        except pyautogui.ImageNotFoundException as err:
            conf -= 0.01
        if conf < 0.88:
            break
    return None


def main(game_region=None):
    # Check if we should run at all.
    proceed = False
    settings = datalink.fetch_json("settings.json")
    try:
        proceed = settings["RepairUpgrade"]["upgrade"]
    except KeyError:
        pass
    if not proceed:
        print("---\nSkipping Repair Upgrade")
        return None
    # Check if we already upgraded Crew Repair today.
    already_complete = False
    today_jst = datetime.now(pytz.timezone('Asia/Tokyo'))
    today_jst_filename = r"data\{}.json".format(today_jst.strftime("%Y-%m-%d"))
    current = datalink.fetch_json(today_jst_filename)
    if "RepairUpgrade" in current.keys():
        already_complete = current["RepairUpgrade"]["already_complete"]
    if already_complete:
        print("---\nSkipping Repair Upgrade")
        return None
    # Select a crewmember at random to begin.
    level_label = find_image(r"images\RepairUpgrade_levelnum.png", area=game_region)
    pyautogui.click(pyautogui.center(level_label))
    sleep(2)
    # Find relevant buttons and build search zones.
    print("---\nStarting Repair Upgrade")
    next_btn = find_image(r"images\RepairUpgrade_next.png", area=game_region)
    next_pos = pyautogui.center(next_btn)
    level_btn = find_image(r"images\RepairUpgrade_levelup.png", area=game_region)
    level_pos = pyautogui.center(level_btn)
    cancel_area = (next_btn[0] - 2*next_btn[2], next_btn[1] - 5*next_btn[3], 3*next_btn[2], 5*next_btn[3])
    skill_tab = find_image(r"images\RepairUpgrade_skilltab.png", area=game_region)
    tab_area = (skill_tab[0] - skill_tab[2]//2, skill_tab[1] - skill_tab[3]//2, 6*skill_tab[2], 2*skill_tab[3])
    # Fetch number of crew to upgrade, then cycle through them.
    try:
        quantity = int(settings["RepairUpgrade"]["crew_qty"])
    except KeyError:
        quantity = 77   # The maximum number of Crew, unless they add more eventually.
    try:
        emergency = int(settings["RepairUpgrade"]["emergency"])
    except KeyError:
        emergency = 20
    for i in range(quantity):
        sub_btn = find_image(r"images\RepairUpgrade_subtab.png", area=tab_area)
        if sub_btn:
            pyautogui.click(pyautogui.center(sub_btn))
            sleep(0.5)
        check = 0
        cancel_btn = None
        while not cancel_btn:
            if check >= emergency:
                break
            pyautogui.click(level_pos)
            sleep(0.3)
            cancel_btn = find_image(r"images\RepairUpgrade_cancel.png", area=cancel_area)
            check += 1
        if cancel_btn:
            pyautogui.click(pyautogui.center(cancel_btn))
            sleep(0.3)
        pyautogui.click(next_pos)
        sleep(3)    # This can probably be shorter, but if the game lags we might waste Training Cores.
    current["RepairUpgrade"] = {"already_complete": True}
    datalink.save_json(today_jst_filename, current)


if __name__ == "__main__":
    print("entered repairupgrade")
    sleep(2)
    main(None)
