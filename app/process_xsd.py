import logging.config
from xmlschema import XMLSchema
from xmlschema.validators.complex_types import XsdComplexType
from xmlschema.validators.simple_types import XsdAtomicRestriction, XsdAtomicBuiltin
from xmlschema.validators.elements import XsdElement
from xmlschema.validators import XsdGroup, XsdComponent

# Get the config parameters
import app_config

logger = logging.getLogger('app.' + __name__)


def clean_string(description: str):
    """
    Remove newline characters, carriage returns, and leading/trailing
    whitespaces from a string. Return None if the resulting string is empty.

    Args:
      description (str): the string to "clean"

    Returns:
      cleaned string or None if the result is empty
    """
    cleaned = description.replace("\n", " ").replace("\r", "").strip()
    if cleaned == "":
        return None
    else:
        return cleaned


def generate_complex_type_str(component: XsdComplexType):
    """Generate the string representating an XSD complex type. For logging purposes.

    Args:
        component (XsdComplexType): the xsd complex type
    """
    if component.local_name is None or component.prefixed_name is None:
        component_str = f"Anonymous {str(component)}"
    else:
        component_str = f"{component.default_namespace}{component.local_name} ({component.prefixed_name})"
    return component_str


def load_schema(filepath, namespace=None, local_copy_folder=None):
    """
    Load an XML schema from a specified filepath with lax validation

    Args:
      filepath: path to the XML schema file
      namespace: default namespace of the schema. Defaults to None
      local_copy_folder: folder where to store a local of the imported schemas. Defaults to None

    Returns:
      XMLSchema object of the schema after building, None in case of an error
    """
    try:
        _schema = XMLSchema(
            filepath, build=False, validation="lax", namespace=namespace
        )
        _schema.build()

        if local_copy_folder is not None:
            _schema.export(target=local_copy_folder, save_remote=True)

        return _schema

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return None


def process_complex_type(component: XsdComplexType, indent=""):
    """Recursively process the content of an XSD complex type.
    Only processes elements whithin the namespaces mentioned in
    config param 'namespaces_to_process'.

    Args:
        component (XsdComplexType): the xsd type to process
        indent (str): optional, used to indent print outs

    Returns:
        None
    """
    component_str = generate_complex_type_str(component)

    # Only process the target namespaces
    if component.default_namespace not in app_config.get('namespaces_to_process'):
        logger.debug(indent + f"  Ignoring complex type {component_str}")
        return

    logger.debug(indent + f"┌ Processing complex type {component_str}")
    process_annotation(component, indent + "| ")

    if component.has_simple_content():
        # Case of an xs:complexType containing only an xs:simpleContent
        logger.debug(f"{indent}|   xs:simpleContent: {str(component)}")
    else:
        for _component in component.content.iter_model():
            try:
                if type(_component) is XsdElement:
                    process_element(_component, indent + "| ")
                elif type(_component) is XsdGroup:
                    process_group(_component, indent + "| ")
                else:
                    logger.warning(indent + f"  Non-managed type1 {str(_component)}")
            except Exception as e:
                logger.warning(
                    f"Error while processing component {str(_component)}: {str(e)}"
                )
    logger.debug(indent + "└ Completed processing complex type " + component_str)


def process_group(component: XsdGroup, indent=""):
    """Manage the content of an XsdGroup, i.e. a sequence, choice...

    Args:
        component (XsdGroup): the xsd group to process
        indent (str): optional, used to indent print outs
    """
    indent = f"{indent}| "
    logger.debug(indent + str(component))
    process_annotation(component, indent)

    for _component in component.iter_model():
        if type(_component) is XsdElement:
            process_element(_component, indent)
        elif type(_component) is XsdGroup:
            process_group(_component, indent)
        else:
            logger.warning(indent + f"  Non-managed type2 {str(_component)}")


def process_element(component: XsdElement, indent=""):
    """Process the content of a non-global XSD element, i.e. defined whithin the scope of another
     element, typically a complex type.

    Args:
        component (XsdElement): the XSD element to process
        indent (str): optional, used to indent print outs"""
    indent = f"{indent}| "
    process_annotation(component, indent)

    if component.ref is None:
        # Only process named elements, i.e. defined as: <xs:element name="Element" type="ElementType"/>
        # Referenced elements (<xs:element ref='Element'/>) are handled separately
        logger.debug(f"{indent}{str(component)}, type: {str(component.type)}")
        process_annotation(component, indent + "| ")

        # Case of an XsdAtomicBuiltin like: <xs:element name="CommonName" type="xs:string"/>
        if type(component.type) is XsdAtomicBuiltin:
            # Case of an XsdAtomicBuiltin like: <xs:element name="CommonName" type="xs:string"/>
            # is _elem.type.is_simple() equivalent?
            logger.debug(f"{indent}| {str(component)}")

        elif type(component.type) is XsdAtomicRestriction:
            # Case of an enumeration: <xs:simpleType><xs:restriction base="xs:string"><xs:enumeration value=...
            for _enum in component.type.enumeration:
                logger.debug(f"{indent}| {_enum}")

        elif type(component.type) is XsdComplexType:
            if component.type.local_name == "anyType":
                logger.debug(f"{indent}| {str(component)}")
            else:
                # Finally, case when the xs:complexType is "really" a complex type
                process_complex_type(component.type, f"{indent}| ")
        else:
            logger.debug(f"{indent}| | {str(component)}")
    else:
        logger.debug(f"{indent}Ignoring {str(component)}, type: {str(component.type)}")


def process_annotation(component: XsdComponent, indent=""):
    """Turns the annotation of any XsdComponenet into a label

    Args:
        component (XsdComponent): any xsd component that may have an annotation
        indent (str): optional, used to indent print outs
    """
    if (
        component.annotation is not None
        and clean_string(str(component.annotation)) is not None
    ):
        logger.debug(f'{indent}Annotation: "{clean_string(str(component.annotation))}"')


def process_global_element(component: XsdElement):
    """Process a globally-defined, named, typed XSD element,
    i.e. an element retrieved from myschema.iter_globals() and defined as:
    <xs:element name="Element" type="ElementType"/>

    Args:
        component (XsdElement): the XSD element to process

    Returns:
        None
    """
    if component.local_name is None or component.prefixed_name is None:
        component_str = str(component)
    else:
        component_str = f"{component.default_namespace}{component.local_name} ({component.prefixed_name}), type: {str(component.type)}"

    # Only process the target namespaces
    if component.default_namespace not in app_config.get('namespaces_to_process'):
        logger.debug(f"- Ignoring element {component_str}")
        return

    logger.debug(f"Processing element {component_str}")
    if (
        component.annotation is not None
        and clean_string(str(component.annotation)) is not None
    ):
        logger.debug(f'  "{clean_string(str(component.annotation))}"')

    # TODO: generate the RDF property for that element
