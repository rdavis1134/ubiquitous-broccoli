# ubiquitous-broccoli
A very weak auto-clicker for G123's Space Battleship Yamato: Voyagers of Tomorrow

---

G123 produces a variety of browser based games, including one based on Space Battleship Yamato. Unfortunately, not only is the game relatively boring, it also requires quite a bit more effort than it should. Although an auto-clicker function is built into the game already, this project is meant to provide a free alternative for at least some of the more time-intensive activities.

### Installation:
If you plan to run other python programs on your machine, it may be useful to run this one in a virtual environment.

From the project folder, run:

`python -m venv venv` to create a virtual environment,

`venv\Scripts\activate` to activate it, then

`pip install -r requirements.txt` to install the dependencies of this project.

When you're ready to quit the game altogether, or need to use your base python install again, `deactivate`

### Usage:
Couldn't be simpler. `python app.py`

You can also launch each activity individually and independently, by invoking the relevant file. For example: `python crewdispatch.py` will invoke the Crew Dispatch auto-clicker without the rest of the program running.

This program expects to read your settings from settings.json. You can disable activities by renaming or removing them from the file.

---

### Completed:
- Activity Navigation.
- Crew Dispatch.
- Event Item auto-buy / auto-use.
- Repair Auto-Upgrade.

### In progress:
- Like Responder.

### Future:
- Crew Dispatch: Detection of failure to open items.
- CLI interface for people who won't use the settings file.

### No longer pursuing:
- Crew Dispatch: Star search / star filtering. Why: Too many cross detections on star amounts. Confidence values high enough to eliminate them also eliminate items due to the in-game background.

### Known issues:
- Crew Dispatch: Items spawned too close to the center of the screen may not be detected before reaching minimum confidence. If you care about those, you can increase the wait_before_refresh and try them yourself. **Be sure to complete or close them before that time expires!**
- Datalink: Program will crash without saving any new progress if there isn't a data folder at the time of saving.
- Crew Dispatch: If your connection is laggy, the game will not update after the refresh, and the lack of update is both not detected and assumed not to have taken place. The Crew Dispatch handler will continue to click any remaining items on screen (ie: non-completable ones) until it reaches the target number of rounds or you terminate the program. Don't worry, though- the game itself (server-side) is updating where it knows the items to be, not telling your computer about them, and deducting all necessary fuel costs from your account.
- Events: The item buyer infrequently misses the Cancel button, and fails to exit the Buy menu before continuing with the Events sequence. Generally this crashes the program before completion. Re-running Events usually fixes it, but the items are still available for use by you at your leisure.
- Events: The Girl's Night and Repair Event backgrounds prevent detection of the back button, at least intermittently. If calling from the main sequence handler, then that position is already known and can be passed in advance, but if calling `events.py` separately the program is unlikely to complete if either the Girl's Night or Repair Event is running.
- Repair Upgrade: The image detector frequently detects the "Sub" tab in its active state. This is technically a waste of time, but because it only results in a verification that we're definitely leveling Repair, it's not a priority bug.
