from time import sleep
import pyautogui

import datalink
from crewdispatch import main as crewdispatch_start
from events import main as events_start
from repairupgrade import main as repairupgrade_start
from likesresponder import main as likes_start
from mailcollector import main as mail_start


def find_image(img, conf=0.9, area=None):
    # Search for a specified image. Suppresses the Exception when/if it isn't found.
    # Instead of crashing, it decreases the confidence by 0.01 and tries again.
    # image:        The image to search for.
    # conf:         The initial confidence for detection of the target image. Defaults to 0.9.
    # area:         Region of the screen to search in. Defaults to the whole screen, which is fairly slow.
    # Returns:      The location of the image (left, top, width, height) if found.
    # Returns:      None if the image isn't found by/before confidence 0.8.
    while True:
        try:
            return pyautogui.locateOnScreen(img, confidence=conf, region=area)
        except pyautogui.ImageNotFoundException as err:
            # sleep(0.1)
            conf -= 0.01
        if conf < 0.8:
            break
    return None


def find_at_least_one_image(images, area=None):
    # Search for images from a list. Suppresses the Exception when/if they aren't found.
    # Provide it a list of images of the same thing to find whichever one is available first.
    # images:       List of images to search for. Search is conducted in list order.
    # area:         Region of the screen to search in. Defaults to the whole screen, which is fairly slow.
    # Returns:      The location (left, top, width, height) of the first image to be found.
    # Returns:      None if none of the images are found by/before confidence 0.8.
    loc = None
    for image in images:
        if loc:
            break
        loc = find_image(image, area=area)
    return loc


def build_game_area():
    # Build out the main game region. Most activities will be in this area, but some do extend out
    # to either side (eg: Ops, Base, Rooms).
    # Returns:      The location (left, top, width, height) of the main game region.

    # Find the bag, because we know the icons there.
    bag_btn = find_image(r"images\Navigation_bag2.png")
    back_btn = None
    back_pos = None
    if not bag_btn:
        back_btn = find_at_least_one_image([r"images\Navigation_back1.png",
                                            r"images\Navigation_back2.png",
                                            r"images\Navigation_back3.png"])    # Crashes if starting from Limited.
        back_pos = pyautogui.center(back_btn)
    while not bag_btn:
        pyautogui.click(back_pos)
        bag_btn = find_image(r"images\Navigation_bag2.png")
    bag_pos = pyautogui.center(bag_btn)
    pyautogui.click(bag_pos)
    sleep(0.3)
    # We should now be in the bag and can fetch the region from back1 to rooms2.
    if not back_btn:
        back_btn = find_image(r"images\Navigation_back1.png")
    rooms_btn = find_image(r"images\Navigation_rooms2.png")
    game_left = back_btn[0] - 3*back_btn[2]
    if game_left < 0:
        game_left = 0
    game_top = back_btn[1]
    game_width = rooms_btn[0] + 2*rooms_btn[2] - game_left
    game_height = rooms_btn[1] + rooms_btn[3] - game_top
    return (game_left, game_top, game_width, game_height)


def build_navigation_area(bag_btn, game_area):
    # Scrape off the bottom portion of the game area to speed up activity navigation.
    # bag_btn:      Location (left, top, width, height) of the bag button (or any other Nav bar button).
    # game_area:    Location (left, top, width, height) of the main game region.
    # Returns:      Location (left, top, width, height) of a region containing the navigation bar.

    return (game_area[0], bag_btn[1] - bag_btn[3]//2, game_area[2], 2*bag_btn[3])


def return_to_bag(back_pos, nav_area):
    # Return to the bag after each activity.
    # Save some time by passing in the position of the back button and searching
    # only near the navigation bar.

    bag_found = find_image(r"images\Navigation_bag2.png", area=nav_area)
    while not bag_found:
        pyautogui.click(back_pos)
        sleep(0.3)
        bag_found = find_image(r"images\Navigation_bag2.png", area=nav_area)
    bag_pos = pyautogui.center(bag_found)
    pyautogui.click(bag_pos)
    sleep(0.3)


def find_in_base(image, game_area):
    # The screen exceeds its areal bounds in the Base page.
    # Search for an image and expand the region to both sides if it isn't found.
    # If it still isn't found, move the screen left and try again.
    # image:        The image to search for.
    # area:         Region (left, top, width, height) of the screen to search in.
    # Returns:      True if the image was eventually found, False if it wasn't.

    img_btn = find_image(image, area=game_area)
    if img_btn:
        pyautogui.click(pyautogui.center(img_btn))
        return True
    # Expand the search area and check again.
    wider_left = game_area[0] - game_area[2]//2
    if wider_left < 0:
        wider_left = 0
    wider_width = 2*game_area[2]
    wider_area = (wider_left, game_area[1], wider_width, game_area[3])
    img_btn = find_image(image, area=wider_area)
    if img_btn:
        pyautogui.click(pyautogui.center(img_btn))
        return True
    # Move to the left and check one last time.
    start_x = game_area[0] + 5*game_area[2]//6
    start_y = game_area[1] + game_area[3]//5
    pyautogui.moveTo(start_x, start_y)
    end_x = game_area[0] + game_area[2]//6
    pyautogui.dragTo(end_x, start_y)
    img_btn = find_image(image, area=game_area)
    if img_btn:
        pyautogui.click(pyautogui.center(img_btn))
        return True
    return False


def main(settings=None):
    # The launching point for the program itself.
    # Each activity should be contained within a separate python file to avoid polluting this file.
    # This file should only be concerned with localizing the game region, navigating to the
    # starting points of each activity, and then dispatching the calls to the appropriate handler.
    # settings:     Dictionary of user-supplied settings. Defaults to settings.json.

    # Determine the main game region and some reusable landmarks.
    game_area = build_game_area()
    back_btn = find_image(r"images\Navigation_back1.png", area=game_area)
    back_pos = pyautogui.center(back_btn)
    bag_btn = find_image(r"images\Navigation_bag1.png", area=game_area)
    nav_area = build_navigation_area(bag_btn, game_area)
    # Retrieve user settings and shift control to each activity.
    if not settings:
        settings = datalink.fetch_json("settings.json")
    for key in settings.keys():
        left_bag = False
        if key == "CrewDispatch":
            base_btn = find_image(r"images\Navigation_base2.png", area=nav_area)
            if base_btn:
                pyautogui.click(pyautogui.center(base_btn))
                left_bag = True
                crewdispatch_btn = find_in_base(r"images\Base_crewdispatch.png", game_area)
                if crewdispatch_btn:
                    sleep(2)
                    crewdispatch_start(game_area)
                else:
                    print("---\nUnable to locate Crew Dispatch button in Base")
            else:
                print("---\nUnable to navigate to Base for Crew Dispatch")
        if key == "Events":
            ops_btn = find_image(r"images\Navigation_ops2.png")
            if ops_btn:
                pyautogui.click(pyautogui.center(ops_btn))
                left_bag = True
                sleep(2)
                events_start(back_pos=back_pos, game_region=game_area)
            else:
                print("---\nUnable to navigate to Ops for Events")
        if key == "RepairUpgrade":
            crew_btn = find_image(r"images\Navigation_crew2.png")
            if crew_btn:
                pyautogui.click(pyautogui.center(crew_btn))
                left_bag = True
                sleep(2)
                repairupgrade_start(game_area)
            else:
                print("---\nUnable to navigate to Crew for Repair Upgrade")
        if key == "LikesResponder":
            rooms_btn = find_image(r"images\Navigation_rooms2.png")
            if rooms_btn:
                pyautogui.click(pyautogui.center(rooms_btn))
                left_bag = True
                sleep(2)
                likes_start(game_area)
            else:
                print("---\nUnable to navigate to Rooms")
        if key == "MailCollector":
            rooms_btn = find_image(r"images\Navigation_rooms2.png", area=nav_area)
            if rooms_btn:
                pyautogui.click(pyautogui.center(rooms_btn))
                left_bag = True
                sleep(2)
                mail_start(game_area)
            else:
                print("---\nUnable to navigate to Rooms for Mail")
        if left_bag:
            return_to_bag(back_pos, nav_area)


if __name__ == "__main__":
    print("entered app.py")
    sleep(2)
    main()

