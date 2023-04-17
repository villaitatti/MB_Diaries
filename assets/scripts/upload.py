import os

import const
import urllib
import configparser

def _get_credentials(type):
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


def upload(output_path, diary, config):

  diary_dir = os.path.join(output_path, const.turtle_ext)
  credentials = _get_credentials(config)

  for (dir_path, dir_names, file_names) in os.walk(diary_dir, topdown=True):
    
    if len(file_names) > 0:
      
      # Iterate files
      for file_name in file_names:
        
        graph_name = 'https://mbdiaries.itatti.harvard.edu'
        t = os.path.basename(os.path.normpath(dir_path))

        if t == 'diary':
          graph_name += '/resource'

        else:
          graph_name += f'/diary/{diary}' 
        
        graph_name = f'{graph_name}/{t}/{file_name.replace(f".{const.turtle_ext}", "")}/context'

        print(f'\n{graph_name}') 

        r_url = f'{credentials[const.key_upload_endpoint]}rdf-graph-store/?graph={graph_name}'
        
        # DELETE
        print(_del(r_url, credentials))

        # PUT
        print(_post(os.path.join(dir_path, file_name), r_url, credentials))
      
    print(file_names)