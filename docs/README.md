Look - I haven't written any documentation for this yet, but I
figure everything has to start somewhere. 

This is a pretty standard Django app for most intents and purposes.
You'll need to create the database (`manage.py migrate` iirc) - I'm 
targeting SQLite due to the easy deployment, but nothing prevents
using postgres or mysql if that's what you prefer. You'll also need
to create a superuser (`manage.py createsuperuser`) if you want to 
use the admin. It's optional.

The last thing you'll need to do is create the /brewpi_django/secretsettings.py
file. I've created an example of this file called /brewpi_django/secretsettings.py.example
. It's basic, for now.




If you think about the main BrewPi project, you have three main components - BrewPi-www, BrewPi-script, and the BrewPi firmware. This project seeks to replace BrewPi-www, and uses a replacement for BrewPi-script (which is in a subdirectory of the same name). Using this instance of Brewpi-script is **mandatory** for this project to function.


