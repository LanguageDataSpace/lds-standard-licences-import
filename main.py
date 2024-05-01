import json

import pyld
import requests
from rdflib import Graph

FRAME = {
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

    },
    "@type": "odrl:Set",
    "odrl:permission": {"@type": "odrl:Permission", "odrl:duty": {"@type": "odrl:Duty"}},
    "odrl:prohibition": {"@type": "odrl:Prohibition", "odrl:remedy": {"@type": "odrl:Duty"}},
    "odrl:obligation": {"@type": "odrl:Duty", "odrl:consequence": {"@type": "odrl:Duty"}},
    "odrl:target": {"@type": "odrl:AssetCollection"}
}


def get_standard_licence_odrl(licence_id: str) -> dict:
    # Get licence from DALICC API
    url = "https://api.dalicc.net/licenselibrary/license/{}?format=ttl&download=true"
    response = requests.get(url.format(licence_id))
    print('Retrieved licence from DALICC:')
    print(response.text)
    print('\n\n\n')

    # Load licence to RDF graph and export to json-ld
    g = Graph()
    g.parse(data=response.text)
    licence_jsonld_serialized = g.serialize(format='json-ld')

    # Transform json-ld to framed json-ld (tree representation)
    additional_ctx = ["odrl:duty", "odrl:permission", "odrl:prohibition", "odrl:target"]
    data = json.loads(licence_jsonld_serialized)
    #ctx = data.get("@context")
    #for additional in additional_ctx:
    #    data['@context'][additional] = {"@type": "@id"}
    #result = pyld.jsonld.compact(pyld.jsonld.frame(data, FRAME), ctx)
    licence_framed_json_ld = pyld.jsonld.frame(data, FRAME)

    #for additional in additional_ctx:
    #    del licence_framed_json_ld['@context'][additional]

    # Delete duties in permissions - due to error EDC
    # TODO - remove in the future
    if type(licence_framed_json_ld.get('odrl:permission')) == list:
        for p in licence_framed_json_ld.get('odrl:permission'):
            del p['odrl:duty']
    elif type(licence_framed_json_ld.get('odrl:permission')) == dict:
        p = licence_framed_json_ld.get('odrl:permission')
        del p['odrl:duty']
    # Fix odrl:duty property between policy and duty to odrl:obligation
    # TODO - remove if Dalicc fixes the errors
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


def create_policy_on_lds_proxy(edc_policy: dict, lds_policy_url: str):
    response = requests.post(lds_policy_url, json=edc_policy)
    if response.status_code == 200:
        return json.loads(response.text)['data']['@id']
    return None


licences_id = [
    'Apache-2.0',
    'Cc010Universal',
    'CC-BY-4.0',
    'CC-BY-ND-4.0',
    'CC-BY-NC-4.0',
    'CC-BY-SA-4.0',
    'CC-BY-NC-ND-4.0',
    'CC-BY-NC-SA-4.0'
]
lds_proxy_create_policy_endpoint = '{}/api/v1/policy_definitions'
lds_proxy_1 = 'http://ldssetup.ilsp.gr:8081'
lds_proxy_2 = 'http://ldssetup.ilsp.gr:7081'
notes = dict()
notes['lds_proxy_1'] = dict()
notes['lds_proxy_2'] = dict()

for id in licences_id:
    edc_policy = get_standard_licence_odrl(id)

    # Writing to sample.json
    with open("StandardLicences/{}.json".format(id), "w") as outfile:
        outfile.write(json.dumps(edc_policy, indent=4))
    id_proxy1 = create_policy_on_lds_proxy(edc_policy, lds_proxy_create_policy_endpoint.format(lds_proxy_1))
    notes['lds_proxy_1'][id] = id_proxy1
    id_proxy2 = create_policy_on_lds_proxy(edc_policy, lds_proxy_create_policy_endpoint.format(lds_proxy_2))
    notes['lds_proxy_2'][id] = id_proxy2


with open("StandardLicences/notes.json", "w") as notefile:
    notefile.write(json.dumps(notes, indent=4))