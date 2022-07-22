import os
import writer
import const
import datetime
from rdflib import Graph, URIRef, namespace, Namespace, Literal


def write_day_graph(filename, diary, day):

  writer.create_dir(os.path.dirname(os.path.abspath(filename)))
  g = create_day_graph(diary, day)
  g.serialize(destination=filename, format='turtle')


def write_page_graph(filename, diary, day):

  writer.create_dir(os.path.dirname(os.path.abspath(filename)))
  g = create_page_graph(diary, day)
  g.serialize(destination=filename, format='turtle')


def write_diary_graph(filename, diary):

  writer.create_dir(os.path.dirname(os.path.abspath(filename)))
  g = create_diary_graph(diary)
  g.serialize(destination=filename, format='turtle')

# Create graphs


def create_day_graph(diary_number, day):

  g = Graph()

  # Namespaces
  PLATFORM = Namespace('http://www.researchspace.org/resource/system/')
  LDP = Namespace('http://www.w3.org/ns/ldp#')
  CRM = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
  DPUB_ANNOTATION = Namespace(
      'https://mbdiaries.itatti.harvard.edu/document/annotation-schema/')
  CRMDIG = Namespace('http://www.ics.forth.gr/isl/CRMdig/')
  PROV = Namespace('http://www.w3.org/ns/prov#')
  RDF = namespace.RDF
  RDFS = namespace.RDFS
  XSD = namespace.XSD

  day_date = day['date']
  page_number = day['page']
  day_index = day['day']
  day_number = int(day_index) + int(page_number) - 1

  # Day
  DAY_NODE = URIRef(
      f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}/day/{day_index}')
  g.add((DAY_NODE, RDF.type, CRM['E22_Man-Made_Object']))
  g.add((DAY_NODE, CRM.P2_has_type, URIRef(
      'https://mbdiaries.itatti.harvard.edu/ontology/Day')))
  g.add((DAY_NODE, RDFS.label, Literal(
      f'Day #{day_index} ({day_date})', datatype=XSD.string)))
  g.add((DAY_NODE, CRM.P46i_forms_part_of, URIRef(
      f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}')))
  g.add((DAY_NODE, URIRef('https://mbdiaries.itatti.harvard.edu/ontology/order'),
        Literal(day_index, datatype=XSD.integer)))

  # Page
  PAGE_NODE = URIRef(
      f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}/page/{page_number}')
  g.add((DAY_NODE, CRM.P62i_is_depicted_by, PAGE_NODE))

  g.namespace_manager.bind('Platform', PLATFORM, override=True, replace=True)
  g.namespace_manager.bind('crm', CRM, override=True, replace=True)
  g.namespace_manager.bind('crmdig', CRMDIG, override=True, replace=True)
  g.namespace_manager.bind('ldp', LDP, override=True, replace=True)
  g.namespace_manager.bind('prov', PROV, override=True, replace=True)

  return g


def create_page_graph(diary_number, page):

  g = Graph()

  # Namespaces
  PLATFORM = Namespace('http://www.researchspace.org/resource/system/')
  LDP = Namespace('http://www.w3.org/ns/ldp#')
  CRM = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
  DPUB_ANNOTATION = Namespace(
      'https://mbdiaries.itatti.harvard.edu/document/annotation-schema/')
  CRMDIG = Namespace('http://www.ics.forth.gr/isl/CRMdig/')
  PROV = Namespace('http://www.w3.org/ns/prov#')
  RDF = namespace.RDF
  RDFS = namespace.RDFS
  XSD = namespace.XSD

  page_number = page[const.key_index]

  # Page
  PAGE_NODE = URIRef(
      f'https://mbdiaries.itatti.harvard.ed/resource/diary/{diary_number}/page/{page_number}')

  # Page File
  PAGE_NODE_DOCUMENT = URIRef(
      f'https://mbdiaries.itatti.harvard.edu/document/{diary_number}/page/{page_number}')
  g.add((PLATFORM.fileContainer, LDP.contains, PAGE_NODE_DOCUMENT))
  g.add((PAGE_NODE_DOCUMENT, RDF.type, PLATFORM.File))
  g.add((PAGE_NODE_DOCUMENT, RDF.type, LDP.Resource))
  g.add((PAGE_NODE_DOCUMENT, RDF.type, URIRef(
      'https://mbdiaries.itatti.harvard.edu/ontology/Document')))
  g.add((PAGE_NODE_DOCUMENT, RDFS.label, Literal(
      f'LDP Container of document file of {page_number}.html', datatype=XSD.string)))
  g.add((PAGE_NODE_DOCUMENT, PLATFORM.fileContext, URIRef(
      'http://www.researchspace.org/resource/TextDocuments')))
  g.add((PAGE_NODE_DOCUMENT, PLATFORM.fileName, Literal(
      f'{diary_number}_{page_number}.html', datatype=XSD.string)))
  g.add((PAGE_NODE_DOCUMENT, PLATFORM.mediaType,
        Literal('form-data', datatype=XSD.string)))
  g.add((PAGE_NODE_DOCUMENT, PROV.wasAttributedTo, Literal(
      datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), datatype=XSD.dateTime)))
  g.add((PAGE_NODE_DOCUMENT, PROV.generatedAtTime, URIRef(
      'http://www.researchspace.org/resource/admin')))
  g.add((PAGE_NODE, CRM.P129i_is_subject_of, PAGE_NODE_DOCUMENT))

  # Visual representation
  IMAGE_NODE = URIRef(
      f'{const.IIIF_server}{int(const.diary_data[diary_number][const.key_id])+int(page_number)}{const.IIIF_trailer}')
  g.add((IMAGE_NODE, RDF.type, CRM.E38_Image))
  g.add((IMAGE_NODE, RDF.type, URIRef(
      'http://www.researchspace.org/ontology/EX_Digital_Image')))
  g.add((PAGE_NODE, CRM.P183i_has_representation, IMAGE_NODE))

  
  g.add((PAGE_NODE, RDF.type, URIRef('https://mbdiaries.itatti.harvard.edu/ontology/Page')))
  g.add((PAGE_NODE, URIRef('https://mbdiaries.itatti.harvard.edu/ontology/part_of'), URIRef(f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}')))
  
  

  g.namespace_manager.bind('Platform', PLATFORM, override=True, replace=True)
  g.namespace_manager.bind('crm', CRM, override=True, replace=True)
  g.namespace_manager.bind('crmdig', CRMDIG, override=True, replace=True)
  g.namespace_manager.bind('ldp', LDP, override=True, replace=True)
  g.namespace_manager.bind('prov', PROV, override=True, replace=True)

  return g


def create_diary_graph(diary_number):

  g = Graph()

  # Namespaces
  PLATFORM = Namespace('http://www.researchspace.org/resource/system/')
  LDP = Namespace('http://www.w3.org/ns/ldp#')
  CRM = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
  DPUB_ANNOTATION = Namespace(
      'https://mbdiaries.itatti.harvard.edu/document/annotation-schema/')
  CRMDIG = Namespace('http://www.ics.forth.gr/isl/CRMdig/')
  PROV = Namespace('http://www.w3.org/ns/prov#')
  RDF = namespace.RDF
  RDFS = namespace.RDFS
  XSD = namespace.XSD

  diary_uri = f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}'

  # Diary
  BASE_NODE = URIRef(diary_uri)
  g.add((PLATFORM.fileContainer, LDP.contains, BASE_NODE))
  g.add((BASE_NODE, RDF.type, CRM['E22_Man-Made-Object']))
  g.add((BASE_NODE, CRM.P2_has_type, URIRef(
      'https://mbdiaries.itatti.harvard.edu/ontology/Diary')))
  g.add((BASE_NODE, RDFS.label, Literal(diary_number, datatype=XSD.string)))

  # Visual representation
  IMAGE_NODE = URIRef(
      f'{const.IIIF_server}{int(const.diary_data[diary_number][const.key_id]+1)}{const.IIIF_trailer}')
  g.add((BASE_NODE, CRM.P183i_has_representation, IMAGE_NODE))
  g.add((IMAGE_NODE, RDF.type, CRM.E38_Image))
  g.add((IMAGE_NODE, RDF.type, URIRef(
      'http://www.researchspace.org/ontology/EX_Digital_Image')))

  g.namespace_manager.bind('Platform', PLATFORM, override=True, replace=True)
  g.namespace_manager.bind('crm', CRM, override=True, replace=True)
  g.namespace_manager.bind('crmdig', CRMDIG, override=True, replace=True)
  g.namespace_manager.bind('ldp', LDP, override=True, replace=True)
  g.namespace_manager.bind('prov', PROV, override=True, replace=True)

  return g


def write_graphs(output_path, graphs):
  for graph in graphs:
    filename = os.path.join(output_path, const.turtle_ext, f'{graph[const.key_index]}.ttl')
    writer.create_dir(os.path.dirname(os.path.abspath(filename)))
    graph[const.key_graph].serialize(destination=filename, format='turtle')


def pages2graphs(diary, pages):
  graphs = []
  for page in pages:
    graphs.append({
        const.key_index: page[const.key_index],
        const.key_graph: create_page_graph(diary, page)
    })

  # Create Diary graph
  graphs.append({
    const.key_index: diary,
    const.key_graph: create_diary_graph(diary)
  }) 

  return graphs
