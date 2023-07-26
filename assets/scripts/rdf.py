import os
import writer
import const
import datetime
from uuid import uuid4
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


def create_page_graph(diary_number, page_number, page):

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

  # Page
  PAGE_NODE = URIRef(
      f'https://mbdiaries.itatti.harvard.ed/resource/diary/{diary_number}/page/{page_number}')

  # Page File
  PAGE_NODE_DOCUMENT = URIRef(
      f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}/document/{page_number}')
  g.add((PLATFORM.fileContainer, LDP.contains, PAGE_NODE_DOCUMENT))
  g.add((PAGE_NODE_DOCUMENT, RDF.type, PLATFORM.File))
  g.add((PAGE_NODE_DOCUMENT, RDF.type, LDP.Resource))
  g.add((PAGE_NODE_DOCUMENT, RDF.type, URIRef(
      'https://mbdiaries.itatti.harvard.edu/ontology/Document')))
  g.add((PAGE_NODE_DOCUMENT, RDFS.label, Literal(
      f'LDP Container of document file of {diary_number}_{page_number}.html', datatype=XSD.string)))
  g.add((PAGE_NODE_DOCUMENT, PLATFORM.fileContext, URIRef(
      'http://www.researchspace.org/resource/TextDocuments')))
  g.add((PAGE_NODE_DOCUMENT, PLATFORM.fileName, Literal(
      f'{diary_number}_{page_number}.html', datatype=XSD.string)))
  g.add((PAGE_NODE_DOCUMENT, PLATFORM.mediaType,
        Literal('form-data', datatype=XSD.string)))
  g.add((PAGE_NODE_DOCUMENT, PROV.generatedAtTime, Literal(
      datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'), datatype=XSD.dateTime)))
  g.add((PAGE_NODE_DOCUMENT, PROV.wasAttributedTo, URIRef(
      'http://www.researchspace.org/resource/admin')))
  g.add((PAGE_NODE, CRM.P129i_is_subject_of, PAGE_NODE_DOCUMENT))

  # Visual representation
  IMAGE_NODE = URIRef(
      f'{const.IIIF_server}{int(const.diary_data[diary_number][const.key_id])+int(page_number)}{const.IIIF_trailer}')
  g.add((IMAGE_NODE, RDF.type, CRM.E38_Image))
  g.add((IMAGE_NODE, RDF.type, URIRef(
      'http://www.researchspace.org/ontology/EX_Digital_Image')))
  g.add((PAGE_NODE, CRM.P183i_has_representation, IMAGE_NODE))

  if const.key_footnote_header_location_wkt in page:
    g.add((PAGE_NODE, URIRef('https://mbdiaries.itatti.harvard.edu/ontology/hasLocationWkt'), Literal(page[const.key_footnote_header_location_wkt]) ))
  if const.key_footnote_header_location_name in page:
    g.add((PAGE_NODE, URIRef('https://mbdiaries.itatti.harvard.edu/ontology/hasLocationName'), Literal(page[const.key_footnote_header_location_name]) ))
  if const.key_footnote_header_location_link in page:
    g.add((PAGE_NODE, URIRef('https://mbdiaries.itatti.harvard.edu/ontology/hasLocationLink'), Literal(page[const.key_footnote_header_location_link]) ))

  g.add((PAGE_NODE, RDF.type, URIRef('https://mbdiaries.itatti.harvard.edu/ontology/Page')))
  g.add((PAGE_NODE, RDFS.label, Literal(page_number, datatype=XSD.string)))
  #
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

def create_annotation_graph(diary_number, annotation, identifier):

  g = Graph()

  # Namespaces
  PLATFORM = Namespace('http://www.researchspace.org/resource/system/')
  LDP = Namespace('http://www.w3.org/ns/ldp#')
  OA = Namespace('http://www.w3.org/ns/oa#')
  CRM = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
  OWL = Namespace(
      'http://www.w3.org/2002/07/owl#')
  CRMDIG = Namespace('http://www.ics.forth.gr/isl/CRMdig/')
  PROV = Namespace('http://www.w3.org/ns/prov#')
  RDF = namespace.RDF
  RDFS = namespace.RDFS
  XSD = namespace.XSD
  
  DATE_NOW = datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

  annotator_uri = f'http://www.researchspace.org/resource/user/{annotation[const.footnote_annotator]}' if annotation[const.footnote_annotator] is not None else 'http://www.researchspace.org/resource/user/admin'
  annotation_uri = f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}/annotation/{identifier}'
  annotation_source_uri = f'https://mbdiaries.itatti.harvard.edu/diary/{diary_number}/document/{annotation[const.key_footnote_header_page]}'

  ANNOTATION_NODE = URIRef(annotation_uri)
  ANNOTATION_CONTAINER_NODE = URIRef(f'{annotation_uri}/container')

  # LDP container
  g.add( (PLATFORM.formContainer, LDP.contains, ANNOTATION_CONTAINER_NODE) )
  g.add( (ANNOTATION_CONTAINER_NODE, RDF.type, LDP.Resource) )
  g.add( (ANNOTATION_CONTAINER_NODE, RDF.type, PROV.Entity) )
  g.add( (ANNOTATION_CONTAINER_NODE, RDFS.label, Literal(
    f"LDP Container of annotation in diary {diary_number} number {identifier}", datatype=XSD.string)) )
  g.add( (ANNOTATION_CONTAINER_NODE, PROV.wasAttributedTo, URIRef(annotator_uri)) )
  g.add( (ANNOTATION_CONTAINER_NODE, PROV.generatedAtTime, Literal(DATE_NOW, datatype=XSD.dateTime)) )
  
  # Annotation
  g.add( (ANNOTATION_NODE, RDF.type, OA.Annotation) ) 
  g.add( (ANNOTATION_NODE, RDF.type, CRMDIG.D29_Annotation_Object) ) 
  # Annotation Event
  annotation_event_uri = f'{annotation_source_uri}/annotation-event-{uuid4()}'
  ANNOTATION_EVENT_NODE = URIRef(annotation_event_uri)
  g.add( (ANNOTATION_EVENT_NODE, RDF.type, CRMDIG.D30_Annotation_Event) )
  g.add( (ANNOTATION_EVENT_NODE, CRM.P14_carried_out_by, URIRef(annotator_uri)) )
  g.add( (ANNOTATION_NODE, CRMDIG.L48i_was_annotation_created_by, ANNOTATION_EVENT_NODE) )

  # Annotation Event modification
  annotation_event_modification_uri = f'{annotation_event_uri}/modifiedAt'
  ANNOTATION_EVENT_MODIFICATION_NODE = URIRef(annotation_event_modification_uri)
  g.add( (ANNOTATION_EVENT_MODIFICATION_NODE, CRM.P81b_begin_of_the_end, Literal(DATE_NOW, datatype=XSD.dateTime)) )
  g.add( (ANNOTATION_EVENT_MODIFICATION_NODE, CRM.P81a_end_of_the_begin, Literal(DATE_NOW, datatype=XSD.dateTime)) )
  g.add( (ANNOTATION_EVENT_NODE, CRM.P4_has_time_span, ANNOTATION_EVENT_MODIFICATION_NODE) )
  
  # Annotation target
  annotation_target_uri = f'{annotation_source_uri}/range-source-{uuid4()}'
  ANNOTATION_TARGET_NODE = URIRef(annotation_target_uri)
  g.add( (ANNOTATION_TARGET_NODE, RDF.type, OA.SpecificResource) )
  g.add( (ANNOTATION_TARGET_NODE, RDF.value, Literal(annotation[const.footnote_fulltext])) )
  g.add( (ANNOTATION_TARGET_NODE, OA.hasSource, URIRef(annotation_source_uri)) )
  g.add( (ANNOTATION_NODE, OA.hasTarget, ANNOTATION_TARGET_NODE) )

  # Annotation range selector
  annotation_range_selector_uri = f'{annotation_source_uri}/range-{uuid4()}'
  ANNOTATION_RANGE_SELECTOR_NODE = URIRef(annotation_range_selector_uri)
  g.add( (ANNOTATION_RANGE_SELECTOR_NODE, RDF.type, OA.RangeSelector) )  
  g.add( (ANNOTATION_TARGET_NODE, OA.hasSelector, ANNOTATION_RANGE_SELECTOR_NODE) )

  # Start selector
  annotation_range_selector_start_uri = f'{annotation_source_uri}/xpath-{uuid4()}'
  ANNOTATION_RANGE_SELECTOR_START_NODE = URIRef(annotation_range_selector_start_uri)
  g.add( (ANNOTATION_RANGE_SELECTOR_START_NODE, RDF.value, Literal(f'/p[{annotation[const.footnote_index]}]')) )
  g.add( (ANNOTATION_RANGE_SELECTOR_NODE, OA.hasStartSelector, ANNOTATION_RANGE_SELECTOR_START_NODE) )

  # Start offset
  annotation_range_selector_start_offset_uri = f'{annotation_source_uri}/offset-{uuid4()}'
  ANNOTATION_RANGE_SELECTOR_START_OFFSET_NODE = URIRef(annotation_range_selector_start_offset_uri)
  g.add( (ANNOTATION_RANGE_SELECTOR_START_OFFSET_NODE, RDF.type, OA.TextPositionSelector) )
  g.add( (ANNOTATION_RANGE_SELECTOR_START_OFFSET_NODE, OA.start, Literal(annotation[const.footnote_start], datatype=XSD.nonNegativeInteger)) )
  g.add( (ANNOTATION_RANGE_SELECTOR_START_OFFSET_NODE, OA.end, Literal(annotation[const.footnote_start], datatype=XSD.nonNegativeInteger)) )
  g.add( (ANNOTATION_RANGE_SELECTOR_START_NODE, OA.refinedBy, ANNOTATION_RANGE_SELECTOR_START_OFFSET_NODE) )

  # End selector
  annotation_range_selector_end_uri = f'{annotation_source_uri}/xpath-{uuid4()}'
  ANNOTATION_RANGE_SELECTOR_END_NODE = URIRef(annotation_range_selector_end_uri)
  g.add( (ANNOTATION_RANGE_SELECTOR_END_NODE, RDF.type, OA.XPathSelector) )
  g.add( (ANNOTATION_RANGE_SELECTOR_END_NODE, RDF.value, Literal(f'/p[{annotation[const.footnote_index]}]')) )
  g.add( (ANNOTATION_RANGE_SELECTOR_NODE, OA.hasEndSelector, ANNOTATION_RANGE_SELECTOR_END_NODE) )

  # End offset
  annotation_range_selector_end_offset_uri = f'{annotation_source_uri}/offset-{uuid4()}'
  ANNOTATION_RANGE_SELECTOR_END_OFFSET_NODE = URIRef(annotation_range_selector_end_offset_uri)
  g.add( (ANNOTATION_RANGE_SELECTOR_END_OFFSET_NODE, RDF.type, OA.TextPositionSelector) )
  g.add( (ANNOTATION_RANGE_SELECTOR_END_OFFSET_NODE, OA.start, Literal(annotation[const.footnote_end], datatype=XSD.nonNegativeInteger)) )
  g.add( (ANNOTATION_RANGE_SELECTOR_END_OFFSET_NODE, OA.end, Literal(annotation[const.footnote_end], datatype=XSD.nonNegativeInteger)) )
  g.add( (ANNOTATION_RANGE_SELECTOR_END_NODE, OA.refinedBy, ANNOTATION_RANGE_SELECTOR_END_OFFSET_NODE) )

  # Body
  annotation_body_uri = f'{annotation_uri}/body'
  ANNOTATION_BODY_NODE = URIRef(annotation_body_uri)
  g.add( (ANNOTATION_BODY_NODE, RDF.type, URIRef(f'https://mbdiaries.itatti.harvard.edu/ontology/{annotation[const.footnote_type]}')) )
  g.add( (ANNOTATION_BODY_NODE, RDFS.label, Literal(annotation[const.footnote_fulltext], datatype=XSD.string)))
  for permalink in annotation[const.footnote_permalinks]:
    if permalink:
      g.add( (ANNOTATION_BODY_NODE, OWL.sameAs, URIRef(permalink)) )
  g.add( (ANNOTATION_NODE, OA.hasBody, ANNOTATION_BODY_NODE) )
  
  g.namespace_manager.bind('Platform', PLATFORM, override=True, replace=True)
  g.namespace_manager.bind('crm', CRM, override=True, replace=True)
  g.namespace_manager.bind('crmdig', CRMDIG, override=True, replace=True)
  g.namespace_manager.bind('ldp', LDP, override=True, replace=True)
  g.namespace_manager.bind('prov', PROV, override=True, replace=True)
  g.namespace_manager.bind('oa', OA, override=True, replace=True)
  g.namespace_manager.bind('owl', OWL, override=True, replace=True)

  return g

def write_graphs(output_path, graphs, dir=None):
  for key, graph in graphs.items():

    dir_ttl_out = os.path.join(output_path, const.turtle_ext)
    writer.create_dir(os.path.dirname(dir_ttl_out))

    filename = os.path.join(dir_ttl_out, dir, f'{key}.ttl') if dir else os.path.join(dir_ttl_out, f'{key}.ttl')
    writer.create_dir(os.path.dirname(os.path.abspath(filename)))

    graph.serialize(destination=filename, format='turtle')


def footnotes2graphs(diary, footnotes):
  graphs = {}
  for key, footnote in footnotes.items():
    graphs[key] = create_annotation_graph(diary, footnote, key)
  return graphs

def pages2graphs(diary, pages):
  graphs = {}
  for key, page in pages.items():
    graphs[key] = create_page_graph(diary, key, page)
  return graphs

def diary2graphs(diary):
  graphs = {}
  graphs[diary] = create_diary_graph(diary)
  return graphs
