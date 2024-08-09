import rdflib
from rdflib import Graph, Literal, URIRef, BNode
from rdflib.collection import Collection
from rdflib.namespace import RDF, RDFS, XSD, OWL

import logging
import csv
from io import StringIO

logger = logging.getLogger("app." + __name__)


class RdfGraph:
    """
    Class to handle the RDF graph generated
    """

    def __init__(self) -> None:
        self.graph: Graph = rdflib.Graph(bind_namespaces="core")

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

    def serialize(self, format: str = "turtle") -> str:
        """
        Serialize the graph
        """
        return self.graph.serialize(format=format)

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

    def add_oneof_class_members(self, class_uri: str, members: list[str]) -> None:
        """
        Add a class description to the graph, using the owl:oneOf construct.
        Each member (string) is turned into an individual whose URI is build after the URI of the class
        """
        _uri = URIRef(class_uri)

        # Create an rdf:List whose root is just a blank node
        _collection_node = BNode()
        _collection = Collection(self.graph, _collection_node)
        for _member in members:
            _member_uri = URIRef(class_uri + "_" + _member)
            self.graph.add((_member_uri, RDFS.label, Literal(_member)))
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
