# caldav-daily-digest
The original repo has/had issues working with radicale
I also wanted for it to directly send an email, so I forked it here

---
a little python script to put together a daily digest of events, e.g. to 
be run from cron to email to a user

note that this was originally written against the Beehive groupware server
that Oracle sells, when I was an employee forced to dogfood it. it might
be useful for other caldav-speaking servers, offered up strictly in the
hopes that it might be useful for someone.

# dependencies / installation
  - python 3.x
  - caldav
  - icalendar

2024 note: "apt install python3-caldav" is enough now (debian bookworm/12) to get all the dependencies in modern-enough version. The older instructions are left intact below in case they're useful for those in environments that don't have the right bits in their system's package manager.

(pip install -r requirements.txt should work, but as a note, if you end up with caldav <= 0.5 installed, and your system's usernames include an "@", you will need to patch one file by hand in line with this bug report: https://github.com/python-caldav/caldav/issues/11
 for convenience, a patch file has been included that can be applied by running patch -p0 < objects.py.patch wherever you have objects.py installed on your system)

optional but likely: a functioning cron setup to run this
(e.g.: "30  6 * * 1-5 /path/to/caldav-daily-digest.py" to get a list of the day's meetings at 6:30am every workday)

# tested on
linux (debian, python 3.4+, x86)

# license
apache 2
