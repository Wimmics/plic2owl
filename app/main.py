import argparse
import logging, logging.config
import os
from pprint import pformat
from traceback import format_exc
from urllib.request import build_opener, install_opener
from xmlschema import XMLSchema
from xmlschema.validators.complex_types import XsdComplexType
from xmlschema.validators.simple_types import XsdAtomicRestriction
from xmlschema.validators.elements import XsdElement
import yaml
from process_xsd import (
    load_schema,
    process_simple_type_restriction,
    process_complex_type,
    process_element,
    get_namespaces,
)

import application_config
from RdfGraph import graph


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
            _rdf_namespaces.append((_prefix, graph.make_rdf_namespace(_uri)))
    # Add prefix 'xs' in case we would only have 'xsd', as we need it to be exactly 'xs' in the RDF generation
    _rdf_namespaces.append(("xs", "http://www.w3.org/2001/XMLSchema#"))
    return _rdf_namespaces


if __name__ == "__main__":

    try:
        # ----------------------- Initializations --------------------------------

        # Set an new opener for urllib as some webservers return HTTP 403 Forbidden for the default user agent of urllib
        # See https://theorangeone.net/posts/urllib-useragent/
        opener = build_opener()
        opener.addheaders = [("User-Agent", "plic2owl")]
        install_opener(opener)

        # --- Configure logging service
        with open("../config/logging.yml", "rt") as f:
            log_config = yaml.safe_load(f.read())
        logging.config.dictConfig(log_config)
        logger = logging.getLogger("app." + __name__)

        # --- Define inline arguments
        parser = argparse.ArgumentParser(
            description="Convert an XSD shema into an RDF/OWL vocabulary",
            epilog="Example: python ./main.py PlinianCore_AbstractModel_v3.2.2.7.xsd --copy schemas --output plic_ontology.ttl",
        )
        parser.add_argument(
            "schema", help="Local path or URL to the XSD schema to process"
        )
        parser.add_argument(
            "--config",
            dest="config_file",
            help="""Configuration file. Defaults to ../config/default_config.py""",
        )
        parser.add_argument(
            "--copy",
            dest="folder",
            help="""Local folder: if it does not exist, the downloaded schemas are stored locally.
              If it exists, the schemas are reloaded from the local folder.""",
        )
        parser.add_argument(
            "--output",
            dest="output_file",
            help="Output file in RDF Turtle. If not provided, defaults to the standard output.",
        )

        # Parse the inline parameters
        args = parser.parse_args()
        logger.info("Inline parameters: " + pformat(args))

        # --- Load the aplication configuration
        if args.config_file is None:
            application_config.init("../config/default_config.yml")
        else:
            application_config.init(args.config_file)
        logger.info(f"Configuration parameters:\n{pformat(application_config.config)}")

        # --- Load the schema either from path/url or from a local copy
        if args.folder is None:
            logger.info(f"Loading {args.schema}")
            schema = load_schema(
                args.schema, namespace=application_config.get("default_namespace")
            )
        elif not os.path.isdir(args.folder):
            # Download the schemas and store them locally
            logger.info(f"Loading {args.schema} and storing copy to {args.folder}")
            schema = load_schema(
                args.schema,
                namespace=application_config.get("default_namespace"),
                local_copy_folder=args.folder,
            )
        else:
            # Reload locally stored schemas
            logger.info(
                f"Loading {os.path.basename(args.schema)} from local folder {args.folder}"
            )
            schema = load_schema(
                os.path.join(args.folder, os.path.basename(args.schema)),
                namespace=application_config.get("default_namespace"),
            )
        logger.info(f"Schema loaded: {schema}")

        # Create the RDF namespaces from those declared in the XSD
        graph.add_namespaces(make_rdf_namespaces(schema))
        logger.info(f"RDF prefix/namespaces:\n{pformat(graph.get_namespaces())}")
        logger.info("---------------- Initializations completed ------------------")
        logger.info("")

        # ------------------- Process individual XSD components (test) ---------------------

        # Process one: XsdElement e.g.: AudiencesUnstructured, AnnualCycleAtomized, DetailUnstructured, Dataset
        # component = schema.elements["AncillaryData"]
        # process_element(component)

        # Process one XsdComplextype e.g.: BaseElementsType, DistributionType, DistributionAtomizedType, TaxonRecordNameType, TaxonomicDescriptionType, FeedingAtomizedType
        # component = schema.types["DetailType"]
        # process_complex_type(component)

        # ------------------- Process the whole schema ---------------------

        # Process global types and elements
        if True:
            for component in schema.iter_globals():
                if type(component) is XsdComplexType:
                    process_complex_type(component)
                elif type(component) is XsdAtomicRestriction:
                    process_simple_type_restriction(component)
                elif type(component) is XsdElement:
                    process_element(component)
                else:
                    logger.warning(f"Non-managed global component {str(component)}")
        logger.debug("---------------- Graph generation completed ------------------")

        if args.output_file is None:
            print(graph.serialize(format="turtle"))
        else:
            graph.serialize(destination=args.output_file, format="turtle")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.error(format_exc())
