import configparser
import json
import requests


def get_update_token(connector_keycloak_endpoint: str, get_token_payload: dict):
    try:
        response_auth = requests.post(connector_keycloak_endpoint, data=get_token_payload)
        response_auth.raise_for_status()
    except requests.exceptions.HTTPError as err:
        raise SystemExit(err)
    if response_auth.status_code != requests.codes.ok:
        print(f'Error occured during getting token: {response_auth}')
        return None
    # Get access_token and refresh_token
    access_token = response_auth.json()['access_token']
    license_headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    return license_headers


def create_policy_on_lds_proxy(create_policy_url: str, suggest_licence_endpoint: str,
                               connector_keycloak_endpoint: str,
                               get_token_payload: dict,
                               licences_id: list, folder_added: str):
    license_headers = get_update_token(connector_keycloak_endpoint, get_token_payload)
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
        license_params = {
            'exact': 'true',
            'title': title
        }
        response_licence_search = requests.get(suggest_licence_endpoint, headers=license_headers, params=license_params)
        if response_licence_search.status_code == requests.codes.unauthorized and \
                json.loads(response_licence_search.content)[
                    'message'].casefold() == 'Invalid or Expired token.'.casefold():
            license_headers = get_update_token(connector_keycloak_endpoint, get_token_payload)
            response_licence_search = requests.get(suggest_licence_endpoint, headers=license_headers,
                                                   params=license_params)
        found = False
        if response_licence_search.status_code == requests.codes.ok:
            for p_lic in response_licence_search.json()['data']:
                if p_lic['title'] == title:
                    print(f'Found at {p_lic["id"]}')
                    found = True
                    notes[id] = p_lic['id']
                    break
        if not found:
            # Create policy on lds-edc connector
            print(f'Creating policy {id}')
            response_licence_create = requests.post(create_policy_url, headers=license_headers, json=edc_policy)
            if response_licence_create.status_code == requests.codes.unauthorized and \
                json.loads(response_licence_create.content)['message'].casefold() == 'Invalid or Expired token.'.casefold():
                license_headers = get_update_token(connector_keycloak_endpoint, get_token_payload)
                response_licence_create = requests.post(create_policy_url, headers=license_headers, json=edc_policy)
            if response_licence_create.status_code == requests.codes.ok:
                notes[id] = json.loads(response_licence_create.text)['data']['@id']
                print(f'Policy created successfully with {id}')
            else:
                notes[id] = response_licence_create.text
                print(f'Policy creation failed. Error: {response_licence_create.text}')
    return notes


if __name__ == "__main__":
    # Read config file
    config = configparser.ConfigParser()
    config.read('config.ini')
    lds_proxy_create_policy_endpoint = config['DEFAULT']['create_policy_endpoint']
    lds_proxy_suggest_policy_endpoint = config['DEFAULT']['suggest_licence_endpoint']
    lds_keycloak_endpoint = config['DEFAULT']['get_token_endpoint']
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
        keycloak_address = config[section]['keycloak_address']
        get_token_payload = dict()
        get_token_payload['username'] = config[section]['username']
        get_token_payload['password'] = config[section]['password']
        get_token_payload['client_id'] = config['DEFAULT']['client_id']
        get_token_payload['client_secret'] = config[section]['client_secret']
        get_token_payload['grant_type'] = 'password'

        connector_policy_endpoint = lds_proxy_create_policy_endpoint.format(connector_address)
        connector_suggest_policy_endpoint = lds_proxy_suggest_policy_endpoint.format(connector_address)
        connector_keycloak_endpoint = lds_keycloak_endpoint.format(keycloak_address)
        notes[connector_address] = create_policy_on_lds_proxy(connector_policy_endpoint,
                                                              connector_suggest_policy_endpoint,
                                                              connector_keycloak_endpoint,
                                                              get_token_payload,
                                                              licences_id,
                                                              config['DEFAULT']['folder_licences_added']
                                                              )

    with open('notes.json', "w") as notefile:
        notefile.write(json.dumps(notes, indent=4))
