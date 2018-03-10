#Frequently Asked Questions



##### Can I change the temperature format on a beer I've started logging?

No. To prevent inconsistency the log format is permanently set when logging begins to the temperature format associated with the device. If you would like to change the format and restart logging, do the following:

 1. Update the temperature format in control constants to the desired format
 1. Stop logging the existing beer
 1. Start logging a new beer


##### Help - I forgot my Fermentrack login/password!

Thankfully, this is a pretty easy issue to overcome. Django provides the `manage.py` command line script which contains the `createsuperuser` command. To leverage this, do the following (assuming the standard install locations):

 1. Log into your Raspberry Pi via ssh and switch to the user you installed Fermentrack to (generally this can be done with the command `sudo -u fermentrack -i` assuming you installed to the `fermentrack` user)
 1. Change to the user's home directory (`cd ~`)
 1. Enable the virtualenv (`source venv/bin/activate`)
 1. Change to the Fermentrack directory (`cd fermentrack`)
 1. Run the createsuperuser command (`./manage.py createsuperuser`)
 1. Follow the prompts to create a new superuser account
 1. Log into the Fermentrack admin panel and delete/modify the old account. The Fermentrack admin panel can be accessed through the `Settings` page (the gear in the upper right) and clicking the "Django Admin" button.


##### What happens to my beer logs/active profiles/other data if I change the Fermentrack "Preferred Timezone"?

Not much. To prevent this being an issue Fermentrack uses UTC (GMT) internally and converts times to your local timezone on the fly. Feel free to update your preferred timezone as you move, travel, or are otherwise inclined without worrying about how this might impact your existing logs or active profiles. 



