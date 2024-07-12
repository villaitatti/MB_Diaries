import os
import writer
import const
import datetime
from uuid import uuid4
from rdflib import Graph, URIRef, namespace, Namespace, Literal

BASE_URI = 'https://mbdiaries.itatti.harvard.edu/'
RESOURCE = f'{BASE_URI}resource/'

PLATFORM = Namespace('http://www.researchspace.org/resource/system/')
LDP = Namespace('http://www.w3.org/ns/ldp#')
CRM = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
DPUB_ANNOTATION = Namespace(f'{BASE_URI}document/annotation-schema/')
CRMDIG = Namespace('http://www.ics.forth.gr/isl/CRMdig/')
PROV = Namespace('http://www.w3.org/ns/prov#')
MB_DIARIES = Namespace('https://mbdiaries.itatti.harvard.edu/ontology/')
RDF = namespace.RDF
RDFS = namespace.RDFS
XSD = namespace.XSD


"""
Utility functions for creating and writing RDF graphs.
"""


def write_graphs(output_path, graphs, dir=None):
    """
    Writes a collection of graphs to files in turtle format.

    Parameters:
    output_path (str): The path to the directory where the files will be written.
    graphs (dict): A dictionary where the keys are the names of the graphs and the values are the graphs themselves.
    dir (str, optional): The name of a subdirectory to write the files to. Defaults to None.

    Returns:
    None
    """
    for key, graph in graphs.items():

        dir_ttl_out = os.path.join(output_path, const.turtle_ext)
        writer.create_dir(os.path.dirname(dir_ttl_out))

        filename = os.path.join(dir_ttl_out, dir, f'{key}.ttl') if dir else os.path.join(
            dir_ttl_out, f'{key}.ttl')
        writer.create_dir(os.path.dirname(os.path.abspath(filename)))

        graph.serialize(destination=filename, format='turtle')


"""
Create and write functions for diary graphs.
"""


def write_diary_graph(filename, diary):
    """
    Writes a diary graph to a file in turtle format.

    This function first creates a directory for the file if it doesn't exist.
    Then it creates a diary graph for the given diary.
    Finally, it serializes the graph and writes it to the specified file in turtle format.

    Parameters:
    filename (str): The name of the file to write the graph to.
    diary (object): The diary object to create the diary graph from.

    Returns:
    None
    """
    writer.create_dir(os.path.dirname(os.path.abspath(filename)))
    # Pass the missing argument 'filename'
    g = create_diary_graph(filename, diary)
    g.serialize(destination=filename, format='turtle')


def create_diary_graph(diary_number, image, title, index):
    """
    Creates a diary graph in RDF format.

    This function creates a graph for a specific diary. It adds nodes and edges to the graph
    to represent the diary, its attributes, and its relationships with other entities such as the image.

    Parameters:
    diary_number (int): The number of the diary.
    image (str): The URI of the image representing the diary.

    Returns:
    Graph: The created graph in RDF format.
    """
    g = Graph()

    diary_uri = f'{RESOURCE}diary/{diary_number}'

    # Update diary title
    diary_title = f'Diary {index}'
    if title is not None:
        diary_title = f'{diary_title}, {title}'

    # Diary
    BASE_NODE = URIRef(diary_uri)
    g.add((PLATFORM.fileContainer, LDP.contains, BASE_NODE))
    g.add((BASE_NODE, RDF.type, CRM['E22_Man-Made-Object']))
    g.add((BASE_NODE, CRM.P2_has_type, MB_DIARIES['Diary']))
    g.add((BASE_NODE, RDFS.label, Literal(diary_title, datatype=XSD.string)))
    g.add((BASE_NODE, MB_DIARIES['order'], Literal(index, datatype=XSD.integer)))

    # Visual representation
    IMAGE_NODE = URIRef(image)
    g.add((BASE_NODE, CRM.P183i_has_representation, IMAGE_NODE))
    g.add((IMAGE_NODE, RDF.type, CRM.E38_Image))
    g.add((IMAGE_NODE, RDF.type, URIRef('http://www.researchspace.org/ontology/EX_Digital_Image')))

    g.namespace_manager.bind('Platform', PLATFORM, override=True, replace=True)
    g.namespace_manager.bind('crm', CRM, override=True, replace=True)
    g.namespace_manager.bind('crmdig', CRMDIG, override=True, replace=True)
    g.namespace_manager.bind('ldp', LDP, override=True, replace=True)
    g.namespace_manager.bind('prov', PROV, override=True, replace=True)
    g.namespace_manager.bind('mbdiaries-ontology', MB_DIARIES, override=True, replace=True)

    return g


def diary2graphs(diary, manifest, title, index):
    """
    Converts a diary into a collection of graphs.

    Parameters:
    diary (object): The diary object to convert.
    manifest (dict): A dictionary containing the manifest of the diary.

    Returns:
    dict: A dictionary where the key is the name of the diary and the value is the corresponding graph.
    """
    front = manifest['sequences'][0]['canvases'][0]['images'][0]['resource']['@id']
    graphs = {}
    graphs[diary] = create_diary_graph(diary, front, title, index)
    return graphs


"""
Create and write functions for page graphs.
"""


def write_page_graph(filename, diary, day):
    """
    Writes a page graph to a file in turtle format.

    This function first creates a directory for the file if it doesn't exist.
    Then it creates a page graph for the given diary and day.
    Finally, it serializes the graph and writes it to the specified file in turtle format.

    Parameters:
    filename (str): The name of the file to write the graph to.
    diary (object): The diary object to create the page graph from.
    day (dict): A dictionary containing the page, day, and image for the graph.

    Returns:
    None
    """
    writer.create_dir(os.path.dirname(os.path.abspath(filename)))
    g = create_page_graph(diary, day['page'], day['day'], day['image'])
    g.serialize(destination=filename, format='turtle')


def create_page_graph(diary_number, page_number, page, image):
    """
    Creates a page graph in RDF format.

    This function creates a graph for a specific page in a diary. It adds nodes and edges to the graph
    to represent the page, its attributes, and its relationships with other entities such as the diary, the image, and the metadata.

    Parameters:
    diary_number (int): The number of the diary the page belongs to.
    page_number (int): The number of the page in the diary.
    page (dict): A dictionary containing information about the page, including the location and metadata.
    image (str): The URI of the image representing the page.

    Returns:
    Graph: The created graph in RDF format.
    """
    g = Graph()

    # Page
    PAGE_NODE = URIRef(
        f'{RESOURCE}diary/{diary_number}/page/{page_number}')

    # Page File
    PAGE_NODE_DOCUMENT = URIRef(
        f'{BASE_URI}diary/{diary_number}/document/{page_number}')
    g.add((PLATFORM.fileContainer, LDP.contains, PAGE_NODE_DOCUMENT))
    g.add((PAGE_NODE_DOCUMENT, RDF.type, PLATFORM.File))
    g.add((PAGE_NODE_DOCUMENT, RDF.type, LDP.Resource))
    g.add((PAGE_NODE_DOCUMENT, RDF.type, URIRef(
        f'{BASE_URI}ontology/Document')))
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
    IMAGE_NODE = URIRef(image)
    g.add((IMAGE_NODE, RDF.type, CRM.E38_Image))
    g.add((IMAGE_NODE, RDF.type, URIRef(
        'http://www.researchspace.org/ontology/EX_Digital_Image')))
    g.add((PAGE_NODE, CRM.P183i_has_representation, IMAGE_NODE))

    if const.key_footnote_header_location_wkt in page:
        g.add((PAGE_NODE,  MB_DIARIES['hasLocationWkt'],
              Literal(page[const.key_footnote_header_location_wkt])))
    if const.key_footnote_header_location_name in page:
        g.add((PAGE_NODE, MB_DIARIES['hasLocationName'],
              Literal(page[const.key_footnote_header_location_name])))
    if const.key_footnote_header_location_link in page:
        g.add((PAGE_NODE, URIRef(MB_DIARIES['hasLocationLink']),
              Literal(page[const.key_footnote_header_location_link])))

    g.add((PAGE_NODE, RDF.type, MB_DIARIES['Page']))
    g.add((PAGE_NODE, RDF.type, CRM['E22_Man-Made_Object']))
    g.add((PAGE_NODE, RDFS.label, Literal(page_number, datatype=XSD.string)))
    g.add((PAGE_NODE, MB_DIARIES['index'], Literal(page_number, datatype=XSD.string)))
    g.add((PAGE_NODE, MB_DIARIES['part_of'],
          URIRef(f'{RESOURCE}diary/{diary_number}')))

    # Add date metadata

    if const.key_metadata in page:
        for current_metadata in page[const.key_metadata]:

            if current_metadata["predicate"] == const.key_note_header:

                date_day = current_metadata['object']
                old_day = date_day
                DATE_DAY_NODE = URIRef(f'{RESOURCE}date/{date_day}')
                
                # transform date from yyyy-mm-dd format into DD Month YYYY
                date_day = datetime.datetime.strptime(date_day, '%Y-%m-%d').strftime('%Y %B %d')
                
                # Store production date 
                PAGE_PRODUCTION_NODE = URIRef(f'{RESOURCE}diary/{diary_number}/page/{page_number}/production')
                g.add((PAGE_NODE, CRM.P108i_was_produced_by, PAGE_PRODUCTION_NODE))
                g.add((PAGE_PRODUCTION_NODE, RDF.type, CRM.E12_Production))

                PAGE_PRODUCTION_NODE_DATE = URIRef(f'{RESOURCE}diary/{diary_number}/page/{page_number}/production/date')
                g.add((PAGE_PRODUCTION_NODE, CRM['P4_has_time-span'], PAGE_PRODUCTION_NODE_DATE))
                g.add((PAGE_PRODUCTION_NODE_DATE, RDF.type, CRM.E52_Time_Span))
                g.add((PAGE_PRODUCTION_NODE_DATE, CRM.P86_falls_within, DATE_DAY_NODE))
            
                g.add((DATE_DAY_NODE, RDF.type, CRM.E52_Time_Span))
                g.add((DATE_DAY_NODE, RDFS.label, Literal(date_day, datatype=XSD.string)))
                g.add((DATE_DAY_NODE, RDF.value, Literal(old_day, datatype=XSD.date)))
            
            else:
                g.add((PAGE_NODE, MB_DIARIES[current_metadata["predicate"]], Literal(
                    old_day, datatype=XSD.string)))

    g.namespace_manager.bind('Platform', PLATFORM, override=True, replace=True)
    g.namespace_manager.bind('crm', CRM, override=True, replace=True)
    g.namespace_manager.bind('crmdig', CRMDIG, override=True, replace=True)
    g.namespace_manager.bind('ldp', LDP, override=True, replace=True)
    g.namespace_manager.bind('prov', PROV, override=True, replace=True)
    g.namespace_manager.bind('mbdiaries-ontology',
                             MB_DIARIES, override=True, replace=True)

    return g


def pages2graphs(diary, manifest, pages):
    """
    Converts a collection of pages into a collection of graphs.

    Parameters:
    diary (object): The diary object that the pages belong to.
    manifest (dict): A dictionary containing the manifest of the diary.
    pages (dict): A dictionary where the keys are the names of the pages and the values are the pages themselves.

    Returns:
    dict: A dictionary where the keys are the names of the pages and the values are the corresponding graphs.
    """
    canvases = manifest['sequences'][0]['canvases']
    graphs = {}
    for key, page in pages.items():
        graphs[key] = create_page_graph(
            diary, key, page, canvases[max(key-1, 0)]['images'][0]['resource']['@id'])
    return graphs


"""
Create and write functions for annotation graphs.
"""


def footnotes2graphs(diary, footnotes):
    """
    Converts a collection of footnotes into a collection of graphs.

    Parameters:
    diary (object): The diary object that the footnotes belong to.
    footnotes (dict): A dictionary where the keys are the names of the footnotes and the values are the footnotes themselves.

    Returns:
    dict: A dictionary where the keys are the names of the footnotes and the values are the corresponding graphs.
    """
    graphs = {}
    for key, footnote in footnotes.items():
        graphs[key] = create_annotation_graph(diary, footnote, key)
    return graphs


def create_annotation_graph(diary_number, annotation, identifier):
    """
    Creates an annotation graph in RDF format.

    This function creates a graph for a specific annotation in a diary. It adds nodes and edges to the graph
    to represent the annotation, its attributes, and its relationships with other entities such as the diary, the annotator, and the annotation event.

    Parameters:
    diary_number (int): The number of the diary the annotation belongs to.
    annotation (dict): A dictionary containing information about the annotation, including the annotator, the full text, the start and end points, and the type.
    identifier (str): The identifier of the annotation.

    Returns:
    Graph: The created graph in RDF format.
    """
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

    annotator_uri = f'http://www.researchspace.org/resource/user/{
        annotation[const.footnote_annotator]}' if annotation[const.footnote_annotator] is not None else 'http://www.researchspace.org/resource/user/admin'
    annotation_uri = f'{RESOURCE}diary/{diary_number}/annotation/{identifier}'
    annotation_source_uri = f'{
        BASE_URI}/diary/{diary_number}/document/{annotation[const.key_footnote_header_page]}'

    ANNOTATION_NODE = URIRef(annotation_uri)
    ANNOTATION_CONTAINER_NODE = URIRef(f'{annotation_uri}/container')

    # LDP container
    g.add((PLATFORM.formContainer, LDP.contains, ANNOTATION_CONTAINER_NODE))
    g.add((ANNOTATION_CONTAINER_NODE, RDF.type, LDP.Resource))
    g.add((ANNOTATION_CONTAINER_NODE, RDF.type, PROV.Entity))
    g.add((ANNOTATION_CONTAINER_NODE, RDFS.label, Literal(
        f"LDP Container of annotation in diary {diary_number} number {identifier}", datatype=XSD.string)))
    g.add((ANNOTATION_CONTAINER_NODE, PROV.wasAttributedTo, URIRef(annotator_uri)))
    g.add((ANNOTATION_CONTAINER_NODE, PROV.generatedAtTime,
          Literal(DATE_NOW, datatype=XSD.dateTime)))

    # Annotation
    g.add((ANNOTATION_NODE, RDF.type, OA.Annotation))
    g.add((ANNOTATION_NODE, RDF.type, CRMDIG.D29_Annotation_Object))
    # Annotation Event
    annotation_event_uri = f'{
        annotation_source_uri}/annotation-event-{uuid4()}'
    ANNOTATION_EVENT_NODE = URIRef(annotation_event_uri)
    g.add((ANNOTATION_EVENT_NODE, RDF.type, CRMDIG.D30_Annotation_Event))
    g.add((ANNOTATION_EVENT_NODE, CRM.P14_carried_out_by, URIRef(annotator_uri)))
    g.add((ANNOTATION_NODE, CRMDIG.L48i_was_annotation_created_by, ANNOTATION_EVENT_NODE))

    # Annotation Event modification
    annotation_event_modification_uri = f'{annotation_event_uri}/modifiedAt'
    ANNOTATION_EVENT_MODIFICATION_NODE = URIRef(
        annotation_event_modification_uri)
    g.add((ANNOTATION_EVENT_MODIFICATION_NODE, CRM.P81b_begin_of_the_end,
          Literal(DATE_NOW, datatype=XSD.dateTime)))
    g.add((ANNOTATION_EVENT_MODIFICATION_NODE, CRM.P81a_end_of_the_begin,
          Literal(DATE_NOW, datatype=XSD.dateTime)))
    g.add((ANNOTATION_EVENT_NODE, CRM['P4_has_time-span'],
          ANNOTATION_EVENT_MODIFICATION_NODE))

    # Annotation target
    annotation_target_uri = f'{annotation_source_uri}/range-source-{uuid4()}'
    ANNOTATION_TARGET_NODE = URIRef(annotation_target_uri)
    g.add((ANNOTATION_TARGET_NODE, RDF.type, OA.SpecificResource))
    g.add((ANNOTATION_TARGET_NODE, RDF.value, Literal(
        annotation[const.footnote_fulltext])))
    g.add((ANNOTATION_TARGET_NODE, OA.hasSource, URIRef(annotation_source_uri)))
    g.add((ANNOTATION_NODE, OA.hasTarget, ANNOTATION_TARGET_NODE))

    # Annotation range selector
    annotation_range_selector_uri = f'{annotation_source_uri}/range-{uuid4()}'
    ANNOTATION_RANGE_SELECTOR_NODE = URIRef(annotation_range_selector_uri)
    g.add((ANNOTATION_RANGE_SELECTOR_NODE, RDF.type, OA.RangeSelector))
    g.add((ANNOTATION_TARGET_NODE, OA.hasSelector, ANNOTATION_RANGE_SELECTOR_NODE))

    # Start selector
    annotation_range_selector_start_uri = f'{
        annotation_source_uri}/xpath-{uuid4()}'
    ANNOTATION_RANGE_SELECTOR_START_NODE = URIRef(
        annotation_range_selector_start_uri)
    g.add((ANNOTATION_RANGE_SELECTOR_START_NODE, RDF.value,
          Literal(f'/p[{annotation[const.footnote_index]}]')))
    g.add((ANNOTATION_RANGE_SELECTOR_NODE, OA.hasStartSelector,
          ANNOTATION_RANGE_SELECTOR_START_NODE))

    # Start offset
    annotation_range_selector_start_offset_uri = f'{
        annotation_source_uri}/offset-{uuid4()}'
    ANNOTATION_RANGE_SELECTOR_START_OFFSET_NODE = URIRef(
        annotation_range_selector_start_offset_uri)
    g.add((ANNOTATION_RANGE_SELECTOR_START_OFFSET_NODE,
          RDF.type, OA.TextPositionSelector))
    g.add((ANNOTATION_RANGE_SELECTOR_START_OFFSET_NODE, OA.start, Literal(
        annotation[const.footnote_start], datatype=XSD.nonNegativeInteger)))
    g.add((ANNOTATION_RANGE_SELECTOR_START_OFFSET_NODE, OA.end, Literal(
        annotation[const.footnote_start], datatype=XSD.nonNegativeInteger)))
    g.add((ANNOTATION_RANGE_SELECTOR_START_NODE, OA.refinedBy,
          ANNOTATION_RANGE_SELECTOR_START_OFFSET_NODE))

    # End selector
    annotation_range_selector_end_uri = f'{
        annotation_source_uri}/xpath-{uuid4()}'
    ANNOTATION_RANGE_SELECTOR_END_NODE = URIRef(
        annotation_range_selector_end_uri)
    g.add((ANNOTATION_RANGE_SELECTOR_END_NODE, RDF.type, OA.XPathSelector))
    g.add((ANNOTATION_RANGE_SELECTOR_END_NODE, RDF.value,
          Literal(f'/p[{annotation[const.footnote_index]}]')))
    g.add((ANNOTATION_RANGE_SELECTOR_NODE, OA.hasEndSelector,
          ANNOTATION_RANGE_SELECTOR_END_NODE))

    # End offset
    annotation_range_selector_end_offset_uri = f'{
        annotation_source_uri}/offset-{uuid4()}'
    ANNOTATION_RANGE_SELECTOR_END_OFFSET_NODE = URIRef(
        annotation_range_selector_end_offset_uri)
    g.add((ANNOTATION_RANGE_SELECTOR_END_OFFSET_NODE,
          RDF.type, OA.TextPositionSelector))
    g.add((ANNOTATION_RANGE_SELECTOR_END_OFFSET_NODE, OA.start, Literal(
        annotation[const.footnote_end], datatype=XSD.nonNegativeInteger)))
    g.add((ANNOTATION_RANGE_SELECTOR_END_OFFSET_NODE, OA.end, Literal(
        annotation[const.footnote_end], datatype=XSD.nonNegativeInteger)))
    g.add((ANNOTATION_RANGE_SELECTOR_END_NODE, OA.refinedBy,
          ANNOTATION_RANGE_SELECTOR_END_OFFSET_NODE))

    # Body
    annotation_body_uri = f'{annotation_uri}/body'
    ANNOTATION_BODY_NODE = URIRef(annotation_body_uri)
    g.add((ANNOTATION_BODY_NODE, RDF.type,
          MB_DIARIES[{annotation[const.footnote_type]}]))
    g.add((ANNOTATION_BODY_NODE, RDFS.label, Literal(
        annotation[const.footnote_fulltext], datatype=XSD.string)))
    for permalink in annotation[const.footnote_permalinks]:
        if permalink:
            g.add((ANNOTATION_BODY_NODE, OWL.sameAs, URIRef(permalink)))
    g.add((ANNOTATION_NODE, OA.hasBody, ANNOTATION_BODY_NODE))

    g.namespace_manager.bind('Platform', PLATFORM, override=True, replace=True)
    g.namespace_manager.bind('crm', CRM, override=True, replace=True)
    g.namespace_manager.bind('crmdig', CRMDIG, override=True, replace=True)
    g.namespace_manager.bind('ldp', LDP, override=True, replace=True)
    g.namespace_manager.bind('prov', PROV, override=True, replace=True)
    g.namespace_manager.bind('oa', OA, override=True, replace=True)
    g.namespace_manager.bind('owl', OWL, override=True, replace=True)

    return g


def create_day_graph(diary_number, day):
    """
    Creates a day graph in RDF format.

    This function creates a graph for a specific day in a diary. It adds nodes and edges to the graph
    to represent the day, its attributes, and its relationships with other entities such as the diary and the page.

    Parameters:
    diary_number (int): The number of the diary the day belongs to.
    day (dict): A dictionary containing information about the day, including the date, page number, and day index.

    Returns:
    Graph: The created graph in RDF format.
    """

    g = Graph()

    day_date = day['date']
    page_number = day['page']
    day_index = day['day']

    # Day
    DAY_NODE = URIRef(f'{RESOURCE}diary/{diary_number}/day/{day_index}')
    g.add((DAY_NODE, RDF.type, CRM['E22_Man-Made_Object']))
    g.add((DAY_NODE, CRM.P2_has_type, MB_DIARIES['Day']))
    g.add((DAY_NODE, RDFS.label, Literal(f'Day #{day_index} ({day_date})', datatype=XSD.string)))
    g.add((DAY_NODE, CRM.P46i_forms_part_of, URIRef(f'{RESOURCE}diary/{diary_number}')))
    g.add((DAY_NODE, MB_DIARIES['order'],Literal(day_index, datatype=XSD.integer)))

    # Page
    PAGE_NODE = URIRef(f'{RESOURCE}diary/{diary_number}/page/{page_number}')
    g.add((DAY_NODE, CRM.P62i_is_depicted_by, PAGE_NODE))

    g.namespace_manager.bind('Platform', PLATFORM, override=True, replace=True)
    g.namespace_manager.bind('crm', CRM, override=True, replace=True)
    g.namespace_manager.bind('crmdig', CRMDIG, override=True, replace=True)
    g.namespace_manager.bind('ldp', LDP, override=True, replace=True)
    g.namespace_manager.bind('prov', PROV, override=True, replace=True)

    return g
