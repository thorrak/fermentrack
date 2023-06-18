!! Advanced Users Only !!
Workflow will enable port 443 for the webserver and have it utilize self-signed web certs to use https when accessing the page for better security

Copy both your self-signed .crt and .key files to this folder and uncomment the necessary lines in the Dockerfile to enable https

Total workflow:
1) Copy both your self-signed .crt and .key files to this folder
2) Uncommnent necessary lines in Dockerfile in this folder and change .crt and .key names to your file names
3) Uncommnent necessary lines in nginx.conf and change .crt and .key names to your file names
4) Change to fementrack-tools root directory again
5) `cd ~/fermentrack-tools/`
6) Rebuild the nginx container to push the cert files and updated nginx.conf file to the docker container
7) `docker-compose up -d --build nginx`
8) Verify the container started properly
9) `docker ps`
10) Check functionality at https://IP_ADDRESS of server
