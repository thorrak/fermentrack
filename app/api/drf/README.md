
# Django Rest Framework Endpoints

Additional endpoints for accesing and creating fermentrack resources

## All Resources
List all Endpoints

*http://your-url/api-v1/*

    Response format:  JSON  
    Requires authentication? No

##  Users (POST)

Create Users

    Response format:  JSON  
    Requires authentication? No
    Accept: application/json
    
### Endpoints

> POST - http://your-url/api-v1/create_user - **Create Users** 
> 
> Mandatory Parameters in header : **username**, **password** and **email**.
> 
> Optional Parameters in header: **first_name**,  **last_name**,

###  Request example

    curl -X POST -H "Content-Type: application/json" -d '{"first_name": "Joe", "last_name":"Doe", "username": "joe", "password": "mypass", "email": "joedoe@riseup.net"}' http://your-url/api-v1/create_user/

### Response Example

    {"id":14,"username":"joe","first_name":"Joe","last_name":"Doe","email":"joedoe@riseup.net"}

## Tokens (POST)

This implementation uses  Django Rest Framework JWT Auth https://getblimp.github.io/django-rest-framework-jwt/ for authentications and token management. It also send user data along with token response.
Tokens has as expiration time of 10.000 seconds and non-expired tokens can be "refreshed" to obtain a brand new token with renewed expiration time.

    Response format: JSON 
    Requires authentication? Yes, user password 
    Accept: application/json
  
### Endpoints

> POST - http://your-url/api-token-auth/ - **Create tokens** 

> Mandatory Parameters in header : **username** and **password**  POST - http://your-url/api-token-refresh/ - **Refresh Tokens** 

> Mandatory Parameters in header : **token**

    
###  Request example (Create tokens)

curl -X POST -d "username=joe&password=mypass" http://lyour-url/api-token-auth/

### Response Example
   

    {"email":"joedoe@riseup.net","last_name":"Doe","id":14,"first_name":"Joe","token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImRhbmllbCIsImVtYWlsIjoiZGFuaWZlcm5hbmRvQGdtYWlsLmNvbSIsInVzZXJfaWQiOjEsIm9yaWdfaWF0IjoxNTU3OTUwNDk0LCJleHAiOjE1NTc5NjA0OTR9.TU983_AcLZxzD8UiEBb0uEII35fl5TGPh9wxwM_I2yU"}

## Device (GET/POST)
List Devices and Create new Devices

    Response format:  JSON  
    Requires authentication? Yes

### Endpoints

> POST - http://your-url/devices/  - **Create new Device**

> Mandatory Parameters in header : **token**  

> Mandatory Parameters in body : **device_name** and  **wifi_host_ip**

> GET - http://your-url/devices/ - **List all devices**

> GET - http://your-url/devices/device_id - **List a device**

 
### Request example (Create new Device)

    curl -H "Content-Type: application/json" -X POST -H "Authorization: JWT  <valid_token>" -d '{"device_name" : "brewpi4", "wifi_host_ip":"192.168.1.100"}'  http://your-url/devices/
    
### Response Example

    {"id":4,"device_name":"brewpi4","status":"active","active_profile":null,"temp_format":"C","active_beer_name":"","beer_data":null}

### Request example (List all Devices)

curl -H "Authorization: JWT  
<valid_token>" http://your-url/api-v1/devices/

### Response example 

    [{"id":1,"device_name":"brewpi1","status":"active","active_profile":null,"temp_format":"C","active_beer_name":"Amber Ale","beer_data":null},{"id":2,"device_name":"brewpi2","status":"active","active_profile":1,"temp_format":"C","active_beer_name":"brown ale maturacao","beer_data":null},{"id":3,"device_name":"brewpi3","status":"active","active_profile":null,"temp_format":"C","active_beer_name":"","beer_data":null},{"id":4,"device_name":"brewpi4","status":"active","active_profile":null,"temp_format":"C","active_beer_name":"","beer_data":null}]

## Beers (GET/POST)
List Beers and Create new beer

    Response format:  JSON  
    Requires authentication? Yes
    
### Endpoints

> POST - http://your-url/api-v1/beers/ - **Create new beer**

> Mandatory Parameters in header : **token** 

> Mandatory Parameters in body : **name** and **device_id** (int)

> Optional Parameters in body : **format** ("F" or "C")

> GET - http://your-url/api-v1/beers/  - **List all beers**

> GET - http://your-url/api-v1/beers/beer_id - **List a beer**


### Request example (List all beers)

curl -H "Authorization: JWT  
<valid_token>" http://your-url/api-v1/beers/

### Response example 

    [{"id":2,"name":"brown ale","created":"2019-04-02T18:29:13Z","format":"C","model_version":2,"gravity_enabled":false,"device":1},{"id":5,"name":"Amber Ale","created":"2019-04-02T18:31:05.640886Z","format":"C","model_version":2,"gravity_enabled":false,"device":1},{"id":6,"name":"brown ale maturacao","created":"2019-04-02T18:48:13.308236Z","format":"C","model_version":2,"gravity_enabled":false,"device":1}]
    
### Request example (Create new beer)

    curl -H "Content-Type: application/json" -X POST -H "Authorization: JWT  <valid_token>" -d '{"name" : "brazilian_fruit_beer", "format":"C","device" : 1}'  http://your-url/api-v1/beers/

### Response example 

    {"id":10,"name":"brazilian_fruit_beer","created":"2019-05-15T21:46:13.403686Z","format":"C","model_version":2,"gravity_enabled":false,"device":1}

 
 ##  Profiles
 
## Profiles Points


