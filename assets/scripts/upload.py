import os
from . import const
import configparser
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

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
  command = f'curl -k -u {credentials[const.key_upload_username]}:{
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

  command = f'curl -k -u {credentials[const.key_upload_username]}:{credentials[const.key_upload_password]
                                                                } -X POST -H \'Content-Type: text/turtle\' --data-binary \'@{filename}\' {url}'

  return f'POST\t{os.system(command)}'


def _upload_single_file(file_info, credentials, pbar, lock):
  """
  Upload a single file (DELETE + POST operations).
  
  Parameters:
  file_info (dict): Dictionary containing file path, name, and graph name
  credentials (dict): Authentication credentials
  pbar: Progress bar object
  lock: Threading lock for progress bar updates
  
  Returns:
  tuple: (success, file_name, error_message)
  """
  try:
    file_path = file_info['file_path']
    file_name = file_info['file_name']
    r_url = file_info['url']
    
    # DELETE
    del_result = _del(r_url, credentials)
    
    # POST
    post_result = _post(file_path, r_url, credentials)
    
    # Update progress bar thread-safely
    with lock:
      pbar.update(1)
    
    return (True, file_name, None)
    
  except Exception as e:
    with lock:
      pbar.update(1)
    return (False, file_info['file_name'], str(e))


def upload(output_path, diary, config, max_workers=8):
  """
  Uploads a diary to a specified output path with the provided configuration using parallel processing.

  Parameters:
  output_path (str): The path to upload the diary to.
  diary (object): The diary object to upload.
  config (dict): A dictionary containing the configuration for the upload.
  max_workers (int): Maximum number of concurrent upload threads (default: 8).

  Returns:
  None
  """
  diary_dir = os.path.join(output_path, const.turtle_ext)
  credentials = _get_credentials(config)
  
  # Collect all files to upload
  files_to_upload = []
  
  for (dir_path, dir_names, file_names) in os.walk(diary_dir, topdown=True):
    if len(file_names) > 0:
      for file_name in file_names:
        graph_name = BASE_URI
        t = os.path.basename(os.path.normpath(dir_path))

        if t == 'diary':
          graph_name += f'/resource/{t}/{file_name.replace(f".{const.turtle_ext}", "")}/context'
        elif t == 'annotation':
          graph_name += f'/diary/{diary}/{t}/{file_name.replace(f".{const.turtle_ext}", "")}/container/context'
        else:
          graph_name += f'/diary/{diary}/{t}/{file_name.replace(f".{const.turtle_ext}", "")}/context'

        r_url = f'{credentials[const.key_upload_endpoint]}rdf-graph-store/?graph={graph_name}'
        
        files_to_upload.append({
          'file_path': os.path.join(dir_path, file_name),
          'file_name': file_name,
          'url': r_url
        })

  if not files_to_upload:
    print("No files found to upload.")
    return

  print(f"Starting parallel upload of {len(files_to_upload)} files with {max_workers} workers...")
  
  # Create progress bar and lock for thread-safe updates
  pbar = tqdm(total=len(files_to_upload), desc="Uploading files", unit="file")
  lock = threading.Lock()
  
  # Track results
  successful_uploads = []
  failed_uploads = []
  
  # Use ThreadPoolExecutor for parallel uploads
  with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # Submit all upload tasks
    future_to_file = {
      executor.submit(_upload_single_file, file_info, credentials, pbar, lock): file_info
      for file_info in files_to_upload
    }
    
    # Collect results as they complete
    for future in as_completed(future_to_file):
      success, file_name, error = future.result()
      if success:
        successful_uploads.append(file_name)
      else:
        failed_uploads.append((file_name, error))
  
  pbar.close()
  
  # Print summary
  print(f"\nUpload completed!")
  print(f"Successful uploads: {len(successful_uploads)}")
  if failed_uploads:
    print(f"Failed uploads: {len(failed_uploads)}")
    for file_name, error in failed_uploads:
      print(f"  - {file_name}: {error}")
