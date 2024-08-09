import logging
from xmlschema import XMLSchema
from xmlschema.validators.complex_types import XsdComplexType
from xmlschema.validators.simple_types import XsdAtomicRestriction, XsdAtomicBuiltin
from xmlschema.validators.elements import XsdElement
from xmlschema.validators import XsdGroup, XsdComponent
from rdflib.namespace import XSD

from RdfGraph import graph

# Get the config parameters
import application_config

logger = logging.getLogger("app." + __name__)


def clean_string(description: str) -> str:
    """
    Remove newline characters, carriage returns, and leading/trailing
    whitespaces from a string. Return None if the resulting string is empty.
    """
    cleaned = description.replace("\n", " ").replace("\r", "").strip()
    if cleaned == "":
        return None
    else:
        return cleaned


def make_complex_type_str(component: XsdComplexType) -> str:
    """Generate the string representing an XSD complex type, dependoing on whether this
    is a named or anonymous type. Used for logging purposes.

    Args:
        component (XsdComplexType): the XSD complex type

    Returns:
      formatted type name
    """
    if component.local_name is None or component.prefixed_name is None:
        component_str = f"(anonymous) {str(component)}"
    else:
        component_str = f"{component.default_namespace}{component.local_name} ({component.prefixed_name})"
    return component_str


def make_element_str(component: XsdElement) -> str:
    """Generate the string representating an XSD element, dependoing on whether this
    is a named or anonymous element. Used for logging purposes.

    Args:
        component (XsdElement): the element

    Returns:
      formatted type name
    """

    if component.local_name is None or component.prefixed_name is None:
        component_str = str(component)
    else:
        component_str = f"{component.default_namespace}{component.local_name} ({component.prefixed_name}), type: {str(component.type)}"
    return component_str


def load_schema(filepath, namespace=None, local_copy_folder=None) -> XMLSchema:
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


def process_complex_type(component: XsdComplexType, indent="") -> None:
    """Recursively process the content of an XSD complex type.
    Only processes elements whithin the namespaces mentioned in
    config param 'namespaces_to_process'.

    Args:
        component (XsdComplexType): the xsd type to process
        indent (str): optional, used to indent print outs

    Returns:
        None
    """
    component_str = make_complex_type_str(component)

    # Only process the target namespaces
    if component.default_namespace not in application_config.get("namespaces_to_process"):
        logger.info(indent + f"  Ignoring complex type {component_str}")
        return

    logger.info(indent + f"┌ Processing complex type {component_str}")
    annotation = get_annotation(component)
    if annotation is not None:
        logger.debug(print_annotation(annotation, indent + "| "))

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
                    f"Error while processing component {str(_component)}, parent {str(_component.parent)}: {str(e)}"
                )
    logger.info(indent + "└ Completed processing complex type " + component_str)


def process_group(component: XsdGroup, indent="") -> None:
    """Process the content of an XsdGroup, i.e. a sequence, choice...

    Args:
        component (XsdGroup): the xsd group to process
        indent (str): optional, used to indent print outs
    """
    indent = f"{indent}| "
    logger.debug(indent + str(component))
    annotation = get_annotation(component)
    if annotation is not None:
        logger.debug(print_annotation(annotation, indent))

    for _component in component.iter_model():
        if type(_component) is XsdElement:
            process_element(_component, indent)
        elif type(_component) is XsdGroup:
            process_group(_component, indent)
        else:
            logger.warning(indent + f"  Non-managed type2 {str(_component)}")


def process_element(component: XsdElement, indent="") -> None:
    """Process the content of a non-global XSD element, i.e. defined whithin the scope of another
     element, typically a complex type.

    Args:
        component (XsdElement): the XSD element to process
        indent (str): optional, used to indent print outs"""
    indent = f"{indent}| "

    if component.ref is None:
        # Only process named elements, i.e. defined as: <xs:element name="Element" type="ElementType"/>
        # Referenced elements (<xs:element ref='Element'/>) are handled separately
        logger.debug(f"{indent}{str(component)}, type: {str(component.type)}")
        annotation = get_annotation(component)
        if annotation is not None:
            logger.debug(print_annotation(annotation, indent + "| "))

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
                # Finally, case where the xs:complexType is "really" a complex type,
                # and only if it is anonymous (if it is global, it is already managed separately)
                if component.type.local_name is None:
                    process_complex_type(component.type, f"{indent}| ")
        else:
            logger.debug(f"{indent}| | {str(component)}")
    else:
        logger.debug(f"{indent}Ignoring {str(component)}, type: {str(component.type)}")


def get_annotation(component: XsdComponent) -> None:
    """Returns the annotation of a XsdComponent, or None if empty
    """
    if component.annotation is not None:
        _annot = clean_string(str(component.annotation))
        if _annot is not None:
            return _annot
    return None


def print_annotation(annotation: str, indent: str = None) -> str:
    """Just a pretty print of the annotation for logging purposes, with indentation
    """
    return f'{indent}Annotation: "{annotation[:70]}"'


def process_global_element(component: XsdElement) -> None:
    """Process a globally-defined, named, typed XSD element,
    i.e. an element retrieved from myschema.iter_globals() and defined as:
    <xs:element name="Element" type="ElementType"/>

    Args:
        component (XsdElement): the XSD element to process

    Returns:
        None
    """
    component_str = make_element_str(component)

    # Only process the target namespaces
    if component.default_namespace not in application_config.get("namespaces_to_process"):
        logger.info(f"- Ignoring element {component_str}")
        return

    logger.info(f"Processing global element {component_str}")

    annotation = get_annotation(component)
    if annotation is not None:
        logger.debug(print_annotation(annotation, "  "))

    # Case of an XsdAtomicBuiltin
    if type(component.type) is XsdAtomicBuiltin:
        ptype = component.type.prefixed_name
        if ptype == "xs:string":
            graph.add_datatype_property(component.prefixed_name, description=annotation)
            graph.add_property_domain_range(component.prefixed_name, range=XSD.string)

    # TODO *************************************- TO BE CONTINUED
    elif type(component.type) is XsdAtomicRestriction:
        # Case of an enumeration: <xs:simpleType><xs:restriction base="xs:string"><xs:enumeration value=...
        for _enum in component.type.enumeration:
            logger.debug(f"{_enum}")

    elif type(component.type) is XsdComplexType:
        if component.type.local_name == "anyType":
            logger.debug(f"{component.type}")
        else:
            # Finally, case where the xs:complexType is "really" a complex type,
            # and only if it is anonymous (if it is global, it is already managed separately)
            if component.type.local_name is None:
                # process_complex_type(component.type, f"{indent}| ")
                pass
    else:
        logger.debug(f"{component_str}")
