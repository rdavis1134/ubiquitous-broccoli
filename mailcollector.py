from time import sleep
import pyautogui

import datalink


# settings.json = {
#   "MailCollector" = {
#       "get_mail" = bool       (Whether to collect mail automatically)
#   },
#   ...
# }


def find_image(img, conf=0.9, area=None):
    # Search for a specified image. Suppresses the Exception when/if it isn't found.
    # Instead of crashing, it decreases the confidence by 0.01 and tries again.
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
        proceed = settings["MailCollector"]["get_mail"]
    except KeyError:
        pass
    if not proceed:
        print("---\nSkipping Mail")
        return None
    # Check that we're in Rooms.
    list_btn = find_image(r"images\LikesResponder_list.png", area=game_region)
    if not list_btn:
        print("---\nNot in Rooms, skipping Mail")
        return None
    # Move all the way to the edge.
    print("---\nStarting Mail")
    ops = find_image(r"images\Navigation_Ops2.png", area=game_region)
    rooms = find_image(r"images\Navigation_Rooms1.png", area=game_region)
    left = (ops[0] + ops[2]//2, ops[1] - 5*ops[3]//2)
    right = (rooms[0] + rooms[2]//2, rooms[1] - 5*rooms[3]//2)
    for i in range(5):
        pyautogui.moveTo(left)
        pyautogui.dragTo(right, duration=0.5)
    # Access the mailbox.
    panel_btn = find_image(r"images\MailCollector_openpanel.png")
    if panel_btn:
        pyautogui.click(pyautogui.center(panel_btn))
        sleep(1)
    mail_btn = find_image(r"images\MailCollector_mailbox.png")
    if not mail_btn:
        print("---\nUnable to open the mailbox, skipping Mail")
        return None
    pyautogui.click(pyautogui.center(mail_btn))
    sleep(2)
    # Claim the claimable mail, leave the rest.
    delete_btn = find_image(r"images\MailCollector_delete.png", area=game_region)
    claim_btn = find_image(r"images\MailCollector_claimall.png",
                           area=(delete_btn[0], delete_btn[1] - delete_btn[3]//2, 3*delete_btn[2], 2*delete_btn[3]))
    pyautogui.click(pyautogui.center(claim_btn), clicks=2, interval=1)
    sleep(5)
    ship_btn = find_image(r"images\MailCollector_okay.png", area=game_region)
    if ship_btn:    # Need to check for the Okay button, because it blocks everything else.
        pyautogui.click(pyautogui.center(ship_btn))
    pyautogui.click(pyautogui.center(delete_btn), clicks=2, interval=1)


if __name__ == "__main__":
    print("entered mailcollector.py")
    sleep(2)
    main(None)
