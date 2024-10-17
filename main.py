import configparser
import json

import requests


def create_policy_on_lds_proxy(create_policy_url: str, suggest_licence_endpoint: str,
                               licences_id: list, folder_added: str):
    notes = dict()
    for id in licences_id:
        print(f'Working on policy {id}')
        # Read json-ld file with policy
        f = open(folder_added + '/{}'.format(id), "r")
        # Reading from file
        edc_policy = json.loads(f.read())
        # Closing file
        f.close()

        # Search if policy exists
        print(f'Checking if policy {id} already exists')
        title = edc_policy['policy']['dct:title']['@value']
        payload = {
            'exact': 'true',
            'title': title
        }
        response_licence = requests.get(suggest_licence_endpoint, params=payload)
        found = False
        if response_licence.status_code == requests.codes.ok:
            for p_lic in response_licence.json()['data']:
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
                print(f'Policy created successfully with {id}')
            else:
                notes[id] = response.text
                print(f'Policy creation failed. Error: {response.text}')
    return notes


if __name__ == "__main__":
    # Read config file
    config = configparser.ConfigParser()
    config.read('config.ini')
    lds_proxy_create_policy_endpoint = config['DEFAULT']['create_policy_endpoint']
    lds_proxy_suggest_policy_endpoint = config['DEFAULT']['suggest_licence_endpoint']
    notes = dict()

    # Retrieve licences ids to add to connectors
    print('Retrieve licences ids to add to connectors')
    licences_id = []
    from os import listdir
    from os.path import isfile, join

    licences_id = [f for f in listdir(config['DEFAULT']['folder_licences_added'])
                   if isfile(join(config['DEFAULT']['folder_licences_added'], f))]
    print(licences_id)
    # Add policies to connectors
    print('Adding EDC policies to connectors')

    for section in config.sections():
        connector_address = config[section]['connector_address']
        connector_policy_endpoint = lds_proxy_create_policy_endpoint.format(connector_address)
        connector_suggest_policy_endpoint = lds_proxy_suggest_policy_endpoint.format(connector_address)
        notes[connector_address] = create_policy_on_lds_proxy(connector_policy_endpoint,
                                                              connector_suggest_policy_endpoint,
                                                              licences_id,
                                                              config['DEFAULT']['folder_licences_added']
                                                              )

    with open('notes.json', "w") as notefile:
        notefile.write(json.dumps(notes, indent=4))
