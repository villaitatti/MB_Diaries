import os
from . import const
import configparser
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

BASE_URI = 'https://mbdiaries.itatti.harvard.edu'


def _get_credentials(type):
  """Read username/password/endpoint for the psw.ini section `type`; raises if missing."""
  config = configparser.ConfigParser()
  path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'psw.ini')
  if not config.read(path):
    raise FileNotFoundError(f'{path} not found. Have you created the psw.ini file? see readme.md')
  return {k: config.get(type, k) for k in (
      const.key_upload_username, const.key_upload_password, const.key_upload_endpoint)}


def _upload_single_file(file_info, credentials, pbar, lock):
  """DELETE then POST one graph; returns (success, file_name, error_message)."""
  auth = (credentials[const.key_upload_username], credentials[const.key_upload_password])
  try:
    # params= url-encodes the graph URI; TLS is verified (the old curl -k disabled it).
    params = {'graph': file_info['graph']}
    r = requests.delete(file_info['url'], params=params, auth=auth, timeout=120)
    # 404 = graph not there yet, fine. Anything else: stop before POST so we never half-replace.
    if r.status_code >= 400 and r.status_code != 404:
      return (False, file_info['file_name'], f'DELETE {r.status_code}')
    with open(file_info['file_path'], 'rb') as f:
      r = requests.post(file_info['url'], params=params, auth=auth, data=f,
                        headers={'Content-Type': 'text/turtle'}, timeout=300)
    if r.status_code >= 400:
      return (False, file_info['file_name'], f'POST {r.status_code} (graph was deleted, re-run)')
    return (True, file_info['file_name'], None)
  except Exception as e:
    return (False, file_info['file_name'], str(e))
  finally:
    with lock:
      pbar.update(1)


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

        r_url = f'{credentials[const.key_upload_endpoint]}rdf-graph-store/'
        
        files_to_upload.append({
          'file_path': os.path.join(dir_path, file_name),
          'file_name': file_name,
          'url': r_url,
          'graph': graph_name
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
