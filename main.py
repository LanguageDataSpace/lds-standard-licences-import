import ast
import getopt
import json
import configparser
import sys

import pyld
import requests
from rdflib import Graph, Literal, RDF, Namespace, RDFS, DCTERMS, PROV, FOAF

dalicc_frame = {
    "@context": {
        "cc": "http://creativecommons.org/ns#",
        "dalicc": "https://dalicc.net/ns#",
        "dalicclib": "https://dalicc.net/licenselibrary/",
        "dcmitype": "http://purl.org/dc/dcmitype/",
        "dcat": "http://www.w3.org/ns/dcat#",
        "dct": "http://purl.org/dc/terms/",
        "foaf": "http://xmlns.com/foaf/0.1/",
        "odrl": "http://www.w3.org/ns/odrl/2/",
        "osl": "http://opensource.org/licenses/",
        "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "scho": "http://schema.org/",
        "xsd": "http://www.w3.org/2001/XMLSchema#",
        "prov" : "http://www.w3.org/ns/prov#"
    },
    "@type": "odrl:Set",
    "odrl:permission": {"@type": "odrl:Permission", "odrl:duty": {"@type": "odrl:Duty"}},
    "odrl:prohibition": {"@type": "odrl:Prohibition", "odrl:remedy": {"@type": "odrl:Duty"}},
    "odrl:obligation": {"@type": "odrl:Duty", "odrl:consequence": {"@type": "odrl:Duty"}},
    "prov:wasAttributedTo": {},
}


def retrieve_licences(licences_id: list, folder_init: str, source: str):
    for id in licences_id:
        print(f'Retrieving policy {id} from {source}')
        if source == 'DALICC':
            # Get licence from DALICC API
            url = "https://api.dalicc.net/licenselibrary/license/{}?format=ttl&download=true"
            response = requests.get(url.format(id))
            initial_policy = response.text
        elif source == 'Victor':
            # Get licence from RDF License (Victor's service)
            url = "https://raw.githubusercontent.com/oeg-upm/licensius/master/licensius-ws/src/main/resources/rdflicenses/{}.ttl"
            response = requests.get(url.format(id))
            initial_policy = response.text
        elif source == 'SPDX':
            # Get licence from SPDX
            url = "https://raw.githubusercontent.com/spdx/license-list-data/main/rdfturtle/{}.ttl"
            response = requests.get(url.format(id))
            initial_policy = response.text


        # Write initial license
        with open(folder_init + '/{}.ttl'.format(id), "w") as init_file:
            init_file.write(initial_policy)


def transform_licence_json_ld(licence_text: str, attribution_text: str, spdx_text: str) -> dict:
    # Load licence to RDF graph and export to json-ld
    g = Graph()
    g.parse(data=licence_text)
    g.parse(data=attribution_text)
    if spdx_text is not None:
        g.parse(data=spdx_text)

    # Bind the FOAF namespace to a prefix for more readable output
    odrl = Namespace('http://www.w3.org/ns/odrl/2/')
    g.bind("odrl", odrl)
    # Bind the CC namespace to a prefix for more readable output
    cc = Namespace('http://creativecommons.org/ns#')
    g.bind("cc", cc)
    # Bind the SPDX namespace to a prefix for more readable output
    spdx = Namespace('http://spdx.org/rdf/terms#')
    g.bind("spdx", spdx)

    # Replace odrl:Policy with odrl:Set
    for policy in g.subjects(RDF.type, odrl.Policy):
        g.add((policy, RDF.type, odrl.Set))
        g.remove((policy, RDF.type, odrl.Policy))

    # Victor - Fix name,
    for policy in g.subjects(RDF.type, odrl.Set):
        if (policy, RDFS.label, None) in g:
            init_title = g.value(policy, RDFS.label)
            g.remove((policy, RDFS.label, init_title))
            # If respective spdx licence exists
            if spdx_text is not None:
                # remove rdfs:label, get spdx_name and  copy to dct:title with 'en' lang string
                for spdx_policy in g.subjects(RDF.type, spdx.ListedLicense):
                    title = g.value(spdx_policy, spdx.name)
                    g.add((policy, DCTERMS.title, Literal(title, lang="en")))
            else:
                g.add((policy, DCTERMS.title, Literal(init_title, lang="en")))

    # Victor - if policy.legalcode is Literal copy to dct:description and remove it
    for policy in g.subjects(RDF.type, odrl.Set):
        legal_code = g.value(policy, cc.legalcode)
        if isinstance(legal_code, Literal):
            g.add((policy, DCTERMS.description, legal_code))
            g.remove((policy, cc.legalcode, legal_code))

    # Victor - if policy has seeAlso copy info to cc:legalcode and remove it
    for policy in g.subjects(RDF.type, odrl.Set):
        legal_code = g.value(policy, RDFS.seeAlso)
        if legal_code:
            g.add((policy, cc.legalcode, legal_code))
            g.remove((policy, RDFS.seeAlso, legal_code))

    # Add to policy provenance information
    # Add prov:hadPrimarySource the initial policy IRI
    for policy in g.subjects(RDF.type, odrl.Set):
        g.add((policy, PROV.hadPrimarySource, policy))
    # Add prov:wasAttributedTo the appropriated
    for policy in g.subjects(RDF.type, odrl.Set):
        # Agent
        attribution_to_agent = g.subjects(RDF.type, FOAF.Agent)
        for agent in attribution_to_agent:
            g.add((policy, PROV.wasAttributedTo, agent))
    # Add rdf:type Permission if missing
    for permission in g.objects(None, odrl.permission):
        if (permission, RDF.type, None) not in g:
            g.add((permission, RDF.type, odrl.Permission))
    # Add rdf:type Prohibition if missing
    for prohibition in g.objects(None, odrl.prohibition):
        if (prohibition, RDF.type, None) not in g:
            g.add((prohibition, RDF.type, odrl.Prohibition))
    # Add rdf:type Duty if missing
    for duty in g.objects(None, odrl.obligation):
        if (duty, RDF.type, None) not in g:
            g.add((duty, RDF.type, odrl.Duty))
    for duty in g.objects(None, odrl.duty):
        if (duty, RDF.type, None) not in g:
            g.add((duty, RDF.type, odrl.Duty))
    for duty in g.objects(None, odrl.remedy):
        if (duty, RDF.type, None) not in g:
            g.add((duty, RDF.type, odrl.Duty))
    for duty in g.objects(None, odrl.consequence):
        if (duty, RDF.type, None) not in g:
            g.add((duty, RDF.type, odrl.Duty))

    # Serialize to json-ld
    licence_jsonld_serialized = g.serialize(format='json-ld')

    # Transform json-ld to framed json-ld (tree representation)
    data = json.loads(licence_jsonld_serialized)
    licence_framed_json_ld = pyld.jsonld.frame(data, dalicc_frame)

    # Delete duties in permissions - due to error EDC
    # TODO - remove in the future
    if type(licence_framed_json_ld.get('odrl:permission')) == list:
        for p in licence_framed_json_ld.get('odrl:permission'):
            del p['odrl:duty']
    elif type(licence_framed_json_ld.get('odrl:permission')) == dict:
        p = licence_framed_json_ld.get('odrl:permission')
        del p['odrl:duty']
    # Fix odrl:duty property between policy and duty to odrl:obligation
    if type(licence_framed_json_ld.get('odrl:duty')) == list:
        for d in licence_framed_json_ld.get('odrl:duty'):
            licence_framed_json_ld['odrl:obligation'] = d
        del licence_framed_json_ld['odrl:duty']
    elif type(licence_framed_json_ld.get('odrl:duty')) == dict:
        licence_framed_json_ld['odrl:obligation'] = licence_framed_json_ld['odrl:duty']
        del licence_framed_json_ld['odrl:duty']

    # Add edc:policy wrapper
    edc_licence_framed_json_ld = dict()
    context = licence_framed_json_ld['@context']
    context['edc'] = 'https://w3id.org/edc/v0.0.1/ns/'
    del licence_framed_json_ld['@context']
    edc_licence_framed_json_ld['@context'] = context
    edc_licence_framed_json_ld['edc:policy'] = licence_framed_json_ld
    return edc_licence_framed_json_ld


def transform_licences(licences_id: list, folder_init: str, folder_added: str, prov_attribution_file: str, spdx_licences_id: dict):
    # Read ttl file with provenance attribution
    f = open('./{}'.format(prov_attribution_file), "r")
    prov_attribution_text = f.read()
    f.close()

    for i, id in  enumerate(licences_id):
        print(f'Transforming policy {id}')
        # Read ttl file with policy
        f = open(folder_init + '/{}.ttl'.format(id), "r")
        initial_policy = f.read()
        f.close()

        spdx_policy = None
        if spdx_licences_id is not None and id in spdx_licences_id:
            # Read ttl file with respective SPDX policy
            spdx_id = spdx_licences_id[id]
            print(f'Open spdc file {spdx_id} for policy {id}')
            f = open(folder_init + '/{}.ttl'.format(spdx_id), "r")
            spdx_policy = f.read()
            f.close()

        transformed_policy = transform_licence_json_ld(initial_policy, prov_attribution_text, spdx_policy)
        # Write transformed license
        with open(folder_added + '/{}.json'.format(id), "w") as tranformed_file:
            tranformed_file.write(json.dumps(transformed_policy, indent=4))


def create_policy_on_lds_proxy(create_policy_url: str, suggest_licence_endpoint: str,
                               licences_id: list, folder_added: str):
    notes = dict()
    for id in licences_id:
        print(f'Working on policy {id}')
        # Read json-ld file with policy
        f = open(folder_added+'/{}.json'.format(id), "r")
        # Reading from file
        edc_policy = json.loads(f.read())
        # Closing file
        f.close()

        # Search if policy exists
        print(f'Checking if policy {id} already exists')
        title = edc_policy['edc:policy']['dct:title']['@value']
        payload = {'title': title.split(' ')[0]}
        response_licence = requests.get(suggest_licence_endpoint, params=payload)
        found = False
        if response_licence.status_code == requests.codes.ok:
            for p_lic in response_licence.json():
                if p_lic['title'] == title:
                    print(f'Found at {p_lic["id"]}')
                    found = True
                    notes[id] = p_lic['id']
                    break
        if not found:
            # Create policy on lds-edc connector
            print(f'Creating policy {id}')
            response = requests.post(create_policy_url, json=edc_policy)
            if response.status_code == requests.codes.ok:
                notes[id] = json.loads(response.text)['data']['@id']
            else:
                notes[id] = None
    return notes


if __name__ == "__main__":
    # Read config file
    config = configparser.ConfigParser()
    config.read('config.ini')
    lds_proxy_create_policy_endpoint = config['DEFAULT']['create_policy_endpoint']
    lds_proxy_suggest_policy_endpoint = config['DEFAULT']['suggest_licence_endpoint']
    notes = dict()
    dalicc_licences_id = ast.literal_eval(config['DEFAULT']['dalicc_licences_id'])
    dalicc_attribution_file = config['DEFAULT']['dalicc_attribution_file']

    rdfLicense_licences_id = ast.literal_eval(config['DEFAULT']['rdfLicense_licences_id'])
    rdfLicense_attribution_file = config['DEFAULT']['rdfLicense_attribution_file']

    spdx_id_rdfLicense = ast.literal_eval(config['DEFAULT']['spdx_id_rdfLicense'])
    map_license_to_spdx = ast.literal_eval(config['DEFAULT']['map_license_to_spdx'])

    # Remove 1st argument from the
    # list of command line arguments
    argumentList = sys.argv[1:]

    # Options
    options = "rta"

    # Long options
    long_options = ["Retrieve", "Transform", "Add"]

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argumentList, options, long_options)

        # checking each argument
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-r", "--Retrieve"):
                # Retrieve initial policies and save to file
                print('Retrieving standard lincences as ODRL representation')
                retrieve_licences(dalicc_licences_id,
                                  config['DEFAULT']['folder_licences_init'],
                                  'DALICC')
                retrieve_licences(rdfLicense_licences_id,
                                  config['DEFAULT']['folder_licences_init'],
                                  'Victor')
                retrieve_licences(spdx_id_rdfLicense,
                                  config['DEFAULT']['folder_licences_init'],
                                  'SPDX')
            elif currentArgument in ("-t", "--Transform"):
                # Transform from ttl to edc policy
                print('Transforming to EDC policy representation')
                transform_licences(dalicc_licences_id,
                                   config['DEFAULT']['folder_licences_init'],
                                   config['DEFAULT']['folder_licences_added'],
                                   dalicc_attribution_file,
                                   None
                                   )
                transform_licences(rdfLicense_licences_id,
                                   config['DEFAULT']['folder_licences_init'],
                                   config['DEFAULT']['folder_licences_added'],
                                   rdfLicense_attribution_file,
                                   map_license_to_spdx
                                   )

            elif currentArgument in ("-a", "--Add"):
                # Add policies to connectors
                print('Adding EDC policies to connectors')
                for section in config.sections():
                    connector_address = config[section]['connector_address']
                    connector_policy_endpoint = lds_proxy_create_policy_endpoint.format(connector_address)
                    connector_suggest_policy_endpoint = lds_proxy_suggest_policy_endpoint.format(connector_address)
                    notes[connector_address] = create_policy_on_lds_proxy(connector_policy_endpoint,
                                                                          connector_suggest_policy_endpoint,
                                                                          dalicc_licences_id+rdfLicense_licences_id,
                                                                          config['DEFAULT']['folder_licences_added']
                                                                          )

                with open(config['DEFAULT']['folder_licences_added']+'/notes.json', "w") as notefile:
                    notefile.write(json.dumps(notes, indent=4))
    except getopt.error as err:
        # output error, and return with an error code
        print(str(err))