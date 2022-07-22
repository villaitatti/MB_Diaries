import os
import const
import urllib
import configparser

def _get_credentials(type='localhost'):
  config = configparser.ConfigParser()
  try:
    path = os.path.join(os.path.abspath(os.getcwd()), 'assets', 'scripts', 'psw.ini')
    config.read(path)

    return {
      const.key_upload_username: config.get(type, const.key_upload_username),
      const.key_upload_password: config.get(type, const.key_upload_password),
      const.key_upload_endpoint: config.get(type, const.key_upload_endpoint)
    }
    
  except Exception as ex:
    print('Error. Have you created the psw.ini file? see readme.md')

def _del(url, credentials):

  # curl -v -u admin:admin -X DELETE -H 'Content-Type: text/turtle' http://127.0.0.1:10214/rdf-graph-store?graph=http%3A%2F%2Fdpub.cordh.net%2Fdocument%2FBernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html%2Fcontext
  command = f'curl -u {credentials[const.key_upload_username]}:{credentials[const.key_upload_password]} -X DELETE -H \'Content-Type: text/turtle\' {url}'

  return f'DEL\t{os.system(command)}'


def _post(filename, url, credentials):

    # curl -v -u admin:admin -X POST -H 'Content-Type: text/turtle' --data-binary '@metadata/Bernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html.ttl' http://127.0.0.1:10214/rdf-graph-store?graph=http%3A%2F%2Fdpub.cordh.net%2Fdocument%2FBernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html%2Fcontext

  command = f'curl -u {credentials[const.key_upload_username]}:{credentials[const.key_upload_password]} -X POST -H \'Content-Type: text/turtle\' --data-binary \'@{filename}\' {url}'

  return f'POST\t{os.system(command)}'


def upload(output_path, diary, type='document'):

  diary_dir = os.path.join(output_path, const.turtle_ext)
  credentials = _get_credentials()

  for i, ttl_file in enumerate(os.listdir(diary_dir)):

    file_name = ttl_file.replace(f'.{const.turtle_ext}', '')

    graph_name = f'https://mbdiaries.itatti.harvard.edu/{type}/{diary}/page/{file_name}/context'

    print(f'\n{graph_name}')
    graph_name = urllib.parse.quote(graph_name, safe='')

    r_url = f'{credentials[const.key_upload_endpoint]}rdf-graph-store/?graph={graph_name}'

    # DEL
    print(_del(r_url, credentials))

    # PUT
    print(_post(os.path.join(diary_dir, ttl_file), r_url, credentials))
