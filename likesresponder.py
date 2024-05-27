from time import sleep
from datetime import datetime
import pytz
import pyautogui

import datalink


# settings.json = {
#   "LikesResponder" = {
#       "cutoff_days" = int,    (The earliest age, in days, that is too old to respond to)
#       "use_likes" = bool      (Whether or not we should dispatch Likes at all)
#   },
#   ...
# }


def find_image(img, conf=0.9, stop=0.86, area=None):
    # Search for a specified image. Suppresses the Exception when/if it isn't found.
    # Instead of crashing, it waits a moment then decreases the confidence by 0.01 and tries again.
    # Returns the location of the image (left, top, width, height) if found.
    # Returns None if the image isn't found by/before confidence 0.86.
    while True:
        try:
            return pyautogui.locateOnScreen(img, confidence=conf, region=area)
        except pyautogui.ImageNotFoundException as err:
            conf -= 0.01
        if conf < stop:
            break
    return None


def build_visit_buttons(start: int, threshold: int = 3, game_region=None):
    # Build a list of the Visit buttons currently available.
    # start:            Index of the first Visit button [Required].
    # threshold:        Detection threshold for identical buttons, ||center1 - center2|| <= threshold.
    # game_region:      Where we already expect the game to be on-screen, if available.
    # Returns dictionary of the Visit buttons, accessed by index.

    # Build the list of Visit buttons.
    visit_btns = []
    already_found = []
    for btn in pyautogui.locateAllOnScreen(r"images\LikesResponder_visit.png", confidence=0.9, region=game_region):
        pos = pyautogui.center(btn)
        if pos in already_found:
            continue
        visit_btns.append(btn)
        for i in range(-1*threshold, threshold+1):
            for j in range(-1*threshold, threshold+1):
                already_found.append((pos[0]+i, pos[1]+j))
    # Sort the button list and the appropriate indices, then return the button dictionary.
    keylist = [i for i in range(start, start + len(visit_btns))]
    ordered_btns = sorted(visit_btns, key=lambda button: button[1])
    return dict(zip(keylist, ordered_btns))


def exceeds_cutoff_age(cutoff_days: int, area):
    # Check if an item is too old, based on the age label.
    # Seems like this should be easier to do / require less hard-coding, but it might require OCR.
    # cutoff_days:      The earliest age which is too old and should be skipped.
    # area:             The search area associated with this item.
    # Returns a list of age labels to compare against items to decide they're too old.

    lookback_images = [r"images\LikesResponder_1days.png",
                       r"images\LikesResponder_2days.png",
                       r"images\LikesResponder_3days.png",
                       r"images\LikesResponder_4days.png",
                       r"images\LikesResponder_5days.png"]
    days_old = None
    for img in lookback_images[cutoff_days-1:]:
        days_old = find_image(img, area=area)
        if days_old:
            break
    return (days_old is not None)


def dispatch_like(like_pos, back_pos, boost_region):
    # Dispatch a Like, assuming we're already in the other user's ship.
    # like_pos:     The click position of the Like button.
    # back_pos:     The click position of the Back button.
    # boost_region: The area we expect to see the warning that we need to use a Boost Ticket.
    # Returns True if we aren't yet using Boost Tickets (haven't used all 10 Likes), False otherwise.
    if not like_pos:
        like_btn = find_image(r"images\LikesResponder_like.png")
        like_pos = pyautogui.center(like_btn)
    pyautogui.click(like_pos)
    sleep(1)
    boost = find_image(r"images\LikesResponder_useboost.png", area=boost_region)
    if not back_pos:
        back_btn = find_image(r"images\LikeResponder_back.png")
        back_pos = pyautogui.center(back_btn)
    pyautogui.click(back_pos)
    sleep(1)
    return (boost is None)


def main(game_region=None):
    # Check if we should run at all.
    proceed = False
    settings = datalink.fetch_json("settings.json")
    try:
        proceed = settings["LikesResponder"]["use_likes"]
    except KeyError:
        pass
    if not proceed:
        print("---\nSkipping Likes")
        return None
    # Check if we've already sent out Likes today.
    already_complete = False
    today_jst = datetime.now(pytz.timezone('Asia/Tokyo'))
    today_jst_filename = r"data\{}.json".format(today_jst.strftime("%Y-%m-%d"))
    current = datalink.fetch_json(today_jst_filename)
    if "LikesResponder" in current.keys():
        already_complete = current["LikesResponder"]["already_complete"]
    if already_complete:
        print("---\nSkipping Likes")
        return None
    # Cache Like list location and setup for the Like dispatches.
    print("---\nStarting Likes")
    list_btn = find_image(r"images\LikesResponder_list.png", area=game_region)
    if not list_btn:
        print("\tUnable to open Likes list")
        return None
    list_loc = pyautogui.center(list_btn)
    open_region = game_region
    visit_region = game_region
    boost_region = None
    like_pos = None
    back_pos = None
    try:
        cutoff_days = int(settings["LikesResponder"]["cutoff_days"])
    except KeyError:
        cutoff_days = 0
    # Check the Like list for available Likes to send.
    for i in range(30):
        print("\titem #{}".format(i))
        list_open = None
        while not list_open:
            pyautogui.click(list_loc)
            list_open = find_image(r"images\LikesResponder_listopen.png", area=open_region)
        if (open_region == game_region):    # Cache the search region to confirm the list is open.
            open_region = (list_open[0] - list_open[2], list_open[1] - list_open[3], 3*list_open[2], 3*list_open[3])
        visits = build_visit_buttons(start=0, game_region=visit_region)
        if (visit_region == game_region):   # Cache the search region for the Visit buttons.
            b1 = visits[0]
            b2 = visits[len(visits) - 1]
            visit_region = (b1[0] - b1[2]//2, b1[1] - b1[3], 2*b1[2], b2[1] - b1[1] + 4*b1[3])
        while i not in visits.keys():       # Move list down to the right spot.
            window = sorted(visits.keys())
            first = visits[window[0]]
            last = visits[window[-1]]
            pyautogui.moveTo(last[0] - last[2]//2, last[1] + last[3]//2)
            pyautogui.dragTo(first[0] - first[2]//2, first[1] + first[3]//2, 1, pyautogui.easeOutQuad)
            sleep(0.2)
            visits = build_visit_buttons(window[-1], game_region=visit_region)
        if not boost_region:
            boost_region = (visits[2][0] - visits[2][2], visits[2][1] - visits[2][3], 2*visits[2][2], 3*visits[2][3])
        pyautogui.moveTo(pyautogui.center(visits[i]))
        if cutoff_days:
            age_region = (visits[i][0] - 2*visits[i][2], visits[i][1], 2*visits[i][2], 2*visits[i][3])
            too_old = exceeds_cutoff_age(cutoff_days, age_region)
            if too_old:
                print("\titem age exceeds cutoff")
                break       # We don't have to keep checking, everything further down is even older.
        pyautogui.click(pyautogui.center(visits[i]))
        sleep(1)    # There can be a bit of server lag.
        if not like_pos:    # Cache the Like position.
            like_btn = find_image(r"images\LikesResponder_like.png", area=game_region)
            like_pos = pyautogui.center(like_btn)
        if not back_pos:    # Cache the Back position.
            back_btn = find_image(r"images\LikesResponder_back.png", area=game_region)
            back_pos = pyautogui.center(back_btn)
        keep_looking = dispatch_like(like_pos, back_pos, boost_region)
        if not keep_looking:
            print("\tno more Likes to dispatch")
            break
    current["LikesResponder"] = {"already_complete": True}
    datalink.save_json(today_jst_filename, current)


if __name__ == "__main__":
    print("entered likesresponder.py")
    sleep(2)
    main(None)
