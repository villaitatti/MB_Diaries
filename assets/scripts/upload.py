import os

import const
import configparser
from tqdm import tqdm

BASE_URI = 'https://mbdiaries.itatti.harvard.edu'


def _get_credentials(type):
  """
  Retrieves the credentials for a specific type from a configuration file.

  Parameters:
  type (str): The type of credentials to retrieve.

  Returns:
  dict: A dictionary containing the username, password, and endpoint for the specified type.
  """
  config = configparser.ConfigParser()
  try:
    path = os.path.join(os.path.abspath(os.getcwd()),
                        'assets', 'scripts', 'psw.ini')
    config.read(path)

    return {
        const.key_upload_username: config.get(type, const.key_upload_username),
        const.key_upload_password: config.get(type, const.key_upload_password),
        const.key_upload_endpoint: config.get(type, const.key_upload_endpoint)
    }

  except Exception as ex:
    print('Error. Have you created the psw.ini file? see readme.md')


def _del(url, credentials):
  """
  Sends a DELETE request to a specified URL with the provided credentials.

  Parameters:
  url (str): The URL to send the DELETE request to.
  credentials (dict): A dictionary containing the username and password to use for authentication.

  Returns:
  str: A string containing the result of the DELETE request.
  """
  # curl -v -u admin:admin -X DELETE -H 'Content-Type: text/turtle' http://127.0.0.1:10214/rdf-graph-store?graph=http%3A%2F%2Fdpub.cordh.net%2Fdocument%2FBernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html%2Fcontext
  command = f'curl -u {credentials[const.key_upload_username]}:{
    credentials[const.key_upload_password]} -X DELETE -H \'Content-Type: text/turtle\' {url}'

  return f'DEL\t{os.system(command)}'


def _post(filename, url, credentials):
  """
  Sends a POST request to a specified URL with the provided credentials and file.

  Parameters:
  filename (str): The name of the file to send in the POST request.
  url (str): The URL to send the POST request to.
  credentials (dict): A dictionary containing the username and password to use for authentication.

  Returns:
  str: A string containing the result of the POST request.
  """
  # curl -v -u admin:admin -X POST -H 'Content-Type: text/turtle' --data-binary '@metadata/Bernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html.ttl' http://127.0.0.1:10214/rdf-graph-store?graph=http%3A%2F%2Fdpub.cordh.net%2Fdocument%2FBernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html%2Fcontext

  command = f'curl -u {credentials[const.key_upload_username]}:{credentials[const.key_upload_password]
                                                                } -X POST -H \'Content-Type: text/turtle\' --data-binary \'@{filename}\' {url}'

  return f'POST\t{os.system(command)}'


def upload(output_path, diary, config):
  """
  Uploads a diary to a specified output path with the provided configuration.

  Parameters:
  output_path (str): The path to upload the diary to.
  diary (object): The diary object to upload.
  config (dict): A dictionary containing the configuration for the upload.

  Returns:
  None
  """
  diary_dir = os.path.join(output_path, const.turtle_ext)
  credentials = _get_credentials(config)

  for (dir_path, dir_names, file_names) in os.walk(diary_dir, topdown=True):

    if len(file_names) > 0:
      # Iterate files with progress bar
      for file_name in tqdm(file_names, desc="Uploading files", unit="file"):

        graph_name = BASE_URI
        t = os.path.basename(os.path.normpath(dir_path))

        if t == 'diary':
          graph_name += f'/resource/{t}/{file_name.replace(f".{const.turtle_ext}", "")}/context'

        elif t == 'annotation':
          graph_name += f'/diary/{diary}/{t}/{file_name.replace(f".{const.turtle_ext}", "")}/container/context'

        else:
          graph_name += f'/diary/{diary}/{t}/{file_name.replace(f".{const.turtle_ext}", "")}/context'

        #print(f'\n{graph_name}')

        r_url = f'{credentials[const.key_upload_endpoint]}rdf-graph-store/?graph={graph_name}'

        # DELETE
        _del(r_url, credentials)

        # PUT
        _post(os.path.join(dir_path, file_name), r_url, credentials)

    print(file_names)
