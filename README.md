A script that adds EDC policy representations of standard licences into an LDS-Connector.

**Compatibility Notice:** This version of the code works with LDS-Connector version 0.8.0 and any versions above it. 
It is stable until new releases are introduced.

# Add standard licences into LDS-EDC
## Install requirements
1) Create a python virtual environment using at least python 3.8 `python3 -m venv venv` 
2) Activate python virtual environment `source venv/bin/activate`
3) Install requirement `pip install -r requirements.txt`

## Update Configuration 
In order to add EDC policy representations from standard licences to your LDS-ECD, 
copy `cp config.ini_sample config.ini` and at the `config.ini` file set the following
information:
1) the LDS-EDC address at the variable `connector_address`, 
2) the Keycloak address at the variable `keycloak_address`,
3) the Keycloak client_secret at the variable `client_secret` for the keycloak client connector-1-proxy,
4) the username of the user with connector admin role at the variable `username` and
5) the password of the user with connector admin role at the variable `password`.
```
[connector_1]
connector_address =  ADDRESS_TO_LDS_CONNECTOR
keycloak_address = ADDRESS_TO_KEYCLOAK
client_secret = KEYCLOAK_CLIENT_SECRET
username = USERNAME_WITH_CONNECTOR_ADMIN_ROLE
password = PASSWORD_WITH_CONNECTOR_ADMIN_ROLE
```
Note that in order to find the value for the client_secret variable you need to go to :
keycloak -> "LDS" realm -> connector-1-proxy client -> Credentials tab -> regenerate client secret and
copy-paste value to client_secret variable in the config file .
Leave the rest of the information within the config file unchanged. This action will add the following standard 
licences (found in folder LicencesToAdd) within your LDS connector:  
* CC-BY-SA-4.0.json
* UnderPSI
* cc-by2.5se 
* CC-BY-ND-3.0
* CC-BY-NC-SA-3.0
* CC-BY-SA-3.0.json
* CC-BY-NC-SA-2.0 
* CC-BY-4.0
* CC-BY-NC-ND-4.0
* CC-BY-3.0
* Apache-2.0
* CC-BY-NC-4.0
* CC-BY-ND-4.0
* CC-BY-NC-SA-4.0
* CC0-1.0
* CC-BY-NC-ND-3.0
* CC-BY-2.0
* PublicDomain

## Run script ::
`python3 main.py`

