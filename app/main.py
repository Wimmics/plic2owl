# To instal the first time:
# mamba install -c conda-forge xmlschema

import logging.config
import os
import pathlib
from pprint import pformat, pprint
from traceback import print_exc
from urllib.request import build_opener, install_opener
from xmlschema import XMLSchema
from xmlschema.validators.complex_types import XsdComplexType
from xmlschema.validators.elements import XsdElement
import yaml
from process_xsd import (
    load_schema,
    process_complex_type,
    process_global_element,
    get_namespaces,
)

from RdfGraph import graph

# Get the config parameters
import application_config


def make_rdf_namespaces(schema: XMLSchema) -> list[tuple[str, str]]:
    """
    Create a list of RDF namespaces from the namespaces in the XSD schema.
    Proper RDF namespaces need to end with a '/' or '#', unlike in XSD.

    Args:
        schema: an XMLSchema object
    Returns:
        list of tuples (prefix, namespace)
    """
    _rdf_namespaces = []
    for _prefix, _uri in get_namespaces(schema):
        # Ignore the default namespace '' as we'll use only prefixed names
        if _prefix not in [""]:
            if _uri[-1] != "/":
                _uri += "#"
            _rdf_namespaces.append((_prefix, _uri))
    # Add prefix 'xs' in case we would only have 'xsd', as we need it to be exactly 'xs' in the RDF generation
    _rdf_namespaces.append(("xs", "http://www.w3.org/2001/XMLSchema#"))
    return _rdf_namespaces


if __name__ == "__main__":

    try:
        # ----------------------- Initializations --------------------------------

        # Set an new opener for urllib as some webservers return HTTP 403 Forbidden for the default user agent of urllib
        # See https://theorangeone.net/posts/urllib-useragent/
        opener = build_opener()
        opener.addheaders = [("User-Agent", "plic2rdf")]
        install_opener(opener)

        # Configure logging service
        with open("../config/logging.yml", "rt") as f:
            log_config = yaml.safe_load(f.read())
        logging.config.dictConfig(log_config)
        logger = logging.getLogger("app." + __name__)

        # Checking the loaded configuration
        logger.debug(
            f"Loaded configuration parameters:\n{pformat(application_config.config)}"
        )
        logger.info(
            f"Default namespace of imported XSD components: {application_config.get('default_namespace')}"
        )
        logger.info(
            f"Only consider XSD components from these namespaces: {application_config.get('namespaces_to_process')}"
        )

        # Set the path of XSD files
        plic_path = os.path.join(
            pathlib.Path.home(),
            "Documents/Development/PlinianCore/xsd/abstract models/stable version",
        )

        # Read the XML schema: select to either import schemas from source of from local copy
        plic_schema = load_schema(
            # os.path.join(plic_path, "PlinianCore_AbstractModel_v3.2.2.7.xsd"),
            "../schemas/PlinianCore_AbstractModel_v3.2.2.7.xsd",
            namespace=application_config.get("default_namespace"),
        )
        logger.debug(f"Schema loaded: {plic_schema}")

        # Create the RDF namespaces from those declared in the XSD
        graph.add_namespaces(make_rdf_namespaces(plic_schema))
        logger.debug(
            f"Added prefix/namespace declarations to the RDF graph:\n{pformat(graph.get_namespaces())}"
        )
        logger.debug(
            "---------------------------------- Initializations completed --------------------------------------"
        )

        # ----------------------- Process the XSD components  --------------------------------

        # Process one: XsdElement: AnnualCycleAtomized
        component = plic_schema.elements["Audience"]
        #process_global_element(component)

        # Process one XsdComplextype: DistributionType, DistributionAtomizedType, TaxonRecordNameType, TaxonomicDescriptionType,
        #   EcologicalSignificanceType : 2 sous-groups 1 atomized, 1 unstruct
        #   FeedingAtomizedType: elem Thropic est un <xs:complexType> anonyme
        #   BaseElementsType: lement of type xs:string
        component = plic_schema.types["BaseElementsType"]
        process_complex_type(component)

        # Process the whole schema
        if False:
            for component in plic_schema.iter_globals():
                if type(component) is XsdComplexType:
                    process_complex_type(component)
                    #pass
                elif type(component) is XsdElement:
                    #process_global_element(component)
                    pass
                else:
                    logger.warning(f"Non-managed global component {str(component)}")

        logger.debug(
            "---------------------------------- Graph generation completed --------------------------------------"
        )
        print(graph.serialize(format="turtle"))

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        print_exc()
