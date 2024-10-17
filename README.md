A script that adds EDC policy representations of standard licences into an LDS-Connector v0.7.0.

# Add standard licences into LDS-EDC
In order to add EDC policy representations from standard licences to your LDS-ECD, 
1) copy `cp config.ini_sample config.ini`
2) set the LDS-EDC address of the `config.ini` file at the variable `connector_address`. 
```
[connector_1]
connector_address = ADDRESS_TO_LDS_CONNECTOR
```
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

Leave the rest of the information without any changes.
## Use ::
`python main.py`

