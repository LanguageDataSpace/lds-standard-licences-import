A script that retrieves existing representations of standard licences expressed in ODRL v2.2 (https://www.w3.org/TR/odrl-model/),
transforms them into the EDC policy representation, by merging info from multiple sources if required, and add them into an LDS-Connector.

## Retrieve
Retrieve existing RDF representations of standard licences expressed in ODRL v2.2 (https://www.w3.org/TR/odrl-model/ from the following sources
  - SPDX - https://github.com/spdx/license-list-data
  - DALICC - https://api.dalicc.net/docs#/licenselibrary
  - RDF License - https://rdflicense.linkeddata.es/
and stores them in the folder `LicencesInit`

Set which licences to retrieve from which source in the config file
  - From SPDX set variable `spdx_id_rdfLicense`  
  - From DALIICC set variable `dalicc_licences_id`
  - From RDF License set variable `rdfLicense_licences_id`

### Use ::
` python main.py -r `

## Tranform
Transforms existing RDF representations of standard licences expressed in ODRL v2.2 stored in folder `LicencesInit` into the EDC policy
representation. EDC policy representations are stored in folder `LicencesAdded`. 
Transformation involves: 
  -  Replace declaration of `odrl:Policy` with `odrl:Set`
  -  Fix licence name if licence name is set to `rdfs:label` to `dct:title` with 'en' lang string
     - If the respective SPDX licence exists, copy the name from SPDX licence and remove `rdfs:label`,
     - else, copy the value of `rdfs:label` and then remove `rdfs:label`.
  -  If `cc:legalcode` is Literal copy to `dct:description` and remove it.
  -  If policy has `rdfs:seeAlso` copy info to `cc:legalcode` and remove it
  -  Add to policy provenance information
     -  Add `prov:hadPrimarySource` the initial policy IRI
     -  Add `prov:wasAttributedTo` the appropriated Actor
        - Person :: Víctor Rodríguez Doncel
        - Organization :: DALICC - Data Licenses Clearance Center
  - Add `rdf:type odrl:Permission` if missing
  - Add `rdf:type odrl:Prohibition` if missing
  - Add `rdf:type odrl:Duty` if missing
  - Fix `odrl:duty` property between policy and duty to `odrl:obligation`
  - Add `edc:policy` wrapper

To set which licence would be enriched with the respective SPDX licence set the `map_license_to_spdx` variable at the config file
```
map_license_to_spdx = {
      'cc-by2.0': 'CC-BY-2.0',
      'cc-by3.0': 'CC-BY-3.0',
      'cc-by-nd3.0': 'CC-BY-ND-3.0',
      'cc-by-nc-nd3.0': 'CC-BY-NC-ND-3.0',
      'cc-by-nc-sa2.0': 'CC-BY-NC-SA-2.0',
      'cc-by-nc-sa3.0': 'CC-BY-NC-SA-3.0',
      'cc-by-sa3.0': 'CC-BY-SA-3.0',
      }
```

### Use ::
` python main.py -t`

## Add standard licences into LDS-EDC
In order to add the existing standard licences to your LDS-ECD, 
1) copy `cp config.ini_sample config.ini`
2) set the LDS-EDC address of the `config.ini` file at the variable `connector_address`. 
```
[connector_1]
connector_address = ADDRESS_TO_LDS_CONNECTOR
```
Leave the rest of the information within the config file unchanged. This action will add the following standard 
licences (found in folder LicencesAdded) within your LDS connector:  
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
### Use ::
`python main.py -a`

