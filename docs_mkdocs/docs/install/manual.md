# Manual Installation

Unfortunately, these instructions haven't been fully written yet. That said, below is a general overview of what needs to happen:


1. Log into your Raspberry Pi via SSH or pull up a terminal window
1. Install the system-wide packages (nginx, etc.) `sudo apt-get install -y git-core build-essential python-dev python-pip nginx libzmq-dev libevent-dev python-virtualenv`
1. Add the Fermentrack user `useradd -m -G dialout fermentrack`
1. Clone the fermentrack repo `sudo -u fermentrack git clone https://github.com/thorrak/fermentrack.git "/home/fermentrack/fermentrack"`
1. Set up  virtualenv `cd ~fermentrack` `sudo -u fermentrack virtualenv "venv"`
1. Run the fermentrack upgrade script `sudo -u fermentrack ~fermentrack/fermentrack/utils/upgrade.sh`
1. Create the nginx configuration file, link, and restart nginx (See [fermentrack-tools/nginx-configs/default-fermentrack](https://raw.githubusercontent.com/thorrak/fermentrack-tools/master/nginx-configs/default-fermentrack) as an example)

