# Configuring Fermentrack

Once you have finished installing Fermentrack, you are ready to configure it. You will be guided through the configuration process when you first connect to Fermentrack. An overview of this configuration procedure is below.

## User Setup

When you first access a new installation of Fermentrack you will be asked to set up a user account. This account will enable you to configure devices, configure the Fermentrack application, and view brew logs.

Setting up the user account is extremely straightforward:

1. From the root Fermentrack page, click "Continue to guided installation"
1. On the next page, entering the following:
    - **Username** - The username used to log into Fermentrack
    - **Password** - The password for the user account
    - **Email Address** - Currently unused, but may potentially be used later
1. Click "Create new user account"
1. Done!

You're now ready to move on to configuring the site settings.

## Site Settings

After configuring a user account, the next step is to configure Fermentrack. The following are the available configuration options:

* **Brewery Name** - The name displayed in the upper left of each Fermentrack page
* **Date time format** - *Currently Unused* - May be removed in a future update
* **Date time format display** - The date format used on the dashboard of each device
* **Require login for dashboard** - *Currently Unused* - Should users be required to be logged in to *view* the dashboard/logs. Login will still be required to change temperature settings, configuration options, etc.
* **Temperature format** - The preferred (default) temperature format. Used when setting fermentation temperature profiles. Can be overridden per device.

All of these can be updated at any time by clicking on the "gear" icon in the upper right of any Fermentrack page.


## Notes for Advanced Users

#### User Accounts

Currently, Fermentrack has limited access control implemented, and is not designed for multiple user installations. This feature is planned for a later release - once it becomes available, different levels of access will be able to be specified on a per-user basis.

In the mean time if you need multiple user accounts they can be configured using the Django admin interface (accessible via the "gear" icon). Each account will need "superuser" access to be able to use the full functionality of Fermentrack. Please be aware - multiple user access is not officially supported. When access control functionality is implemented, any users created previously through this method will retain full access/control of Fermentrack.

