Frequently Asked Questions
============================


Can I change the temperature format on a beer I've started logging?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

No. To prevent inconsistency the log format is permanently set when logging begins to the temperature format associated
with the device. If you would like to change the format and restart logging, do the following:

#. Update the temperature format in control constants to the desired format
#. Stop logging the existing beer
#. Start logging a new beer


Help - I forgot my Fermentrack login/password!
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Thankfully, this is a pretty easy issue to overcome. Django provides the ``manage.py`` command line script which
contains the ``createsuperuser`` command. For Docker-based installations, there is a script bundled
alongside `fermentrack-tools`_ that leverages this command to create a new user. To use this script:

#. Log into your Raspberry Pi via SSH
#. Change to the ``fermentrack-tools`` directory (e.g. ``cd fermentrack-tools``)
#. Run ``./docker-create-superuser.sh``
#. Follow the prompts to create a new superuser account
#. Log into the Fermentrack admin panel and delete/modify the old account. The Fermentrack admin panel can be accessed through the ``Settings`` page (the gear in the upper right) and clicking the "Django Admin" button.


For non-docker installs, there are a few more steps but it's still pretty easy:

#. Log into your Raspberry Pi via ssh and switch to the user you installed Fermentrack to (generally this can be done with the command ``sudo -u fermentrack -i`` assuming you installed to the ``fermentrack`` user)
#. Change to the user's home directory (``cd ~``)
#. Enable the virtualenv (``source venv/bin/activate``)
#. Change to the Fermentrack directory (``cd fermentrack``)
#. Run the createsuperuser command (``./manage.py createsuperuser``)
#. Follow the prompts to create a new superuser account
#. Log into the Fermentrack admin panel and delete/modify the old account. The Fermentrack admin panel can be accessed through the ``Settings`` page (the gear in the upper right) and clicking the "Django Admin" button.


What happens to my beer logs/active profiles/other data if I change the Fermentrack "Preferred Timezone"?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not much. To prevent this being an issue Fermentrack uses UTC (GMT) internally and converts times to your local timezone
on the fly. Feel free to update your preferred timezone as you move, travel, or are otherwise inclined without worrying
about how this might impact your existing logs or active profiles.
