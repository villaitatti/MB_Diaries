
# Upload metadata


def _del(filename, url):

  # curl -v -u admin:admin -X DELETE -H 'Content-Type: text/turtle' http://127.0.0.1:10214/rdf-graph-store?graph=http%3A%2F%2Fdpub.cordh.net%2Fdocument%2FBernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html%2Fcontext

  command = f'curl -u {tmp1}:{tmp2} -X DELETE -H \'Content-Type: text/turtle\' {url}'

  return f'DEL\t{os.system(command)}'


def _post(filename, url):

    # curl -v -u admin:admin -X POST -H 'Content-Type: text/turtle' --data-binary '@metadata/Bernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html.ttl' http://127.0.0.1:10214/rdf-graph-store?graph=http%3A%2F%2Fdpub.cordh.net%2Fdocument%2FBernard_Berenson_in_Consuma_to_Yashiro_-1149037200.html%2Fcontext

  command = f'curl -u {tmp1}:{tmp2} -X POST -H \'Content-Type: text/turtle\' --data-binary \'@{filename}\' {url}'

  return f'POST\t{os.system(command)}'


def upload(output_path, diary, dir, type):

  diary_dir = os.path.join(output_path, 'ttl', dir)

  for i, ttl_file in enumerate(os.listdir(diary_dir)):

    file_name = ttl_file.replace('.ttl', '')

    graph_name = f'https://mbdiaries.itatti.harvard.edu/{type}/{diary}/{dir}/{file_name}/context'

    print(f'\n{graph_name}')
    graph_name = urllib.parse.quote(graph_name)

    r_url = f'{endpoint}rdf-graph-store/?graph={graph_name}'

    # DEL
    print(_del(ttl_file, r_url))

    # PUT
    print(_post(os.path.join(diary_dir, ttl_file), r_url))
