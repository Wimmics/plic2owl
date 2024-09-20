"""
This module provides the necessary tools to handle the generation of an OWL ontology: 
functinos to create classes, properties, deal with namespaces, etc.

Author: Franck Michel, Université Côte d'Azur, CNRS, Inria
Created: Aug. 2024
"""

import logging
import rdflib
from rdflib import Graph, Literal, URIRef, BNode
from rdflib.collection import Collection
from rdflib.namespace import RDF, RDFS, XSD, OWL
import re
from urllib import parse

logger = logging.getLogger("app." + __name__)

# Get the config parameters
import application_config as config


class RdfGraph:
    """
    Class to handle the RDF graph generated
    """

    def __init__(self) -> None:
        self.graph: Graph = rdflib.Graph(bind_namespaces="core")

    @staticmethod
    def make_rdf_namespace(xsd_namespace: str) -> str:
        if xsd_namespace is None or xsd_namespace == "":
            xsd_namespace = config.get("default_namespace")
            logger.warning("Namespace not provided. Defaulting to " + xsd_namespace)
        if xsd_namespace[-1] != "/":
            xsd_namespace += "#"
        return xsd_namespace

    @staticmethod
    def camel_case_split(s) -> str:
        """
        Transform a Camel-case string into a string with blanks to separate words
        See: https://stackoverflow.com/questions/5020906/python-convert-camel-case-to-space-delimited-using-regex-and-taking-acronyms-in
        """
        s = re.sub(
            r"((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))", r" \1", s, flags=re.VERBOSE
        )
        return s

    def add_namespaces(self, namespaces: list[tuple[str, str]]) -> None:
        for _prefix, _uri in namespaces:
            self.graph.bind(_prefix, _uri)

    def get_namespaces(self) -> list[tuple[str, str]]:
        _namespaces = [
            (_prefix, _uri)
            for _prefix, _uri in self.graph.namespaces()
            if _prefix != ""
        ]
        return _namespaces

    def serialize(self, destination: str = None, format: str = "turtle") -> str:
        """
        Serialize the graph
        """
        if destination is None:
            return self.graph.serialize(format=format)
        else:
            self.graph.serialize(destination=destination, format=format)
            return None

    def add_class(
        self, class_uri: str, label: str = None, description: str = None
    ) -> None:
        """
        Add an OWL class to the graph, along with optional label and description.
        If the class alredy exists, no triples are added

        """
        _uri = URIRef(class_uri)

        if (_uri, RDF.type, OWL.Class) in self.graph:
            logger.warning(f"-- Class {_uri} already exists")
        else:
            self.graph.add((_uri, RDF.type, OWL.Class))
            if label is not None:
                self.graph.add((_uri, RDFS.label, Literal(label)))
            if description is not None:
                self.graph.add((_uri, RDFS.comment, Literal(description)))

    def add_oneof_class_members(
        self, class_uri: str, members: list[str], enum_type: str = None
    ) -> None:
        """
        Add a class description to the graph, using the owl:oneOf construct.
        Each string member is turned into an individual whose URI is build after the URI of the class.
        Each URI member is simply used as is.
        """
        _uri = URIRef(class_uri)

        # Create an rdf:List whose root is just a blank node
        _collection_node = BNode()
        _collection = Collection(self.graph, _collection_node)
        for _member in members:
            if enum_type == "xs:anyURI":
                _member_uri = URIRef(_member.strip())
            else:
                # For a string, create a new URI with that string as a label
                _member_uri = URIRef(
                    class_uri
                    + "_"
                    + parse.quote(
                        re.sub("[!@#$%&*()\[\]{};:,./<>?\|`~=+ ]", "_", _member.strip())
                    )
                )
                self.graph.add(
                    (
                        _member_uri,
                        RDFS.label,
                        Literal(self.camel_case_split(_member.strip()).lower()),
                    )
                )
            _collection.append(_member_uri)

        # Link the collection to the class iwth owl:oneOf
        self.graph.add((_uri, OWL.oneOf, _collection_node))

    def add_datatype_property(
        self, property_uri: str, label: str = None, description: str = None
    ) -> None:
        """
        Add a datatype property to the graph, along with optional label and description
        """
        _uri = URIRef(property_uri)

        if (_uri, RDF.type, OWL.DatatypeProperty) in self.graph:
            logger.warning(f"-- Property {_uri} already exists")
        else:
            self.graph.add((_uri, RDF.type, OWL.DatatypeProperty))
            if label is not None:
                self.graph.add((_uri, RDFS.label, Literal(label)))
            if description is not None:
                self.graph.add((_uri, RDFS.comment, Literal(description)))

    def add_object_property(
        self, property_uri: str, label: str = None, description: str = None
    ) -> None:
        """
        Add a datatype property to the graph, along with optional label and description
        """
        _uri = URIRef(property_uri)

        if (_uri, RDF.type, OWL.ObjectProperty) in self.graph:
            logger.warning(f"-- Property {_uri} already exists")
        else:

            self.graph.add((_uri, RDF.type, OWL.ObjectProperty))
            if label is not None:
                self.graph.add((_uri, RDFS.label, Literal(label)))
            if description is not None:
                self.graph.add((_uri, RDFS.comment, Literal(description)))

    def add_property_domain_range(
        self, property_uri: str, domain: str = None, range: str = None
    ) -> None:
        """
        Add domain and range to a datatype or object property
        """
        _uri = URIRef(property_uri)
        if domain is not None:
            self.graph.add((_uri, RDFS.domain, URIRef(domain)))
        if range is not None:
            self.graph.add((_uri, RDFS.range, URIRef(range)))


# Global graph object
graph: RdfGraph = RdfGraph()
