import rdflib
from rdflib import Graph, Literal, URIRef
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

    def add_class(
        self, class_uri: str, label: str = None, description: str = None
    ) -> None:
        """
        Add an OWL class to the graph, along with optional label and description
        """
        _uri = URIRef(class_uri)
        self.graph.add((_uri, RDF.type, OWL.Class))
        if label is not None:
            self.graph.add((_uri, RDFS.label, Literal(label)))
        if description is not None:
            self.graph.add((_uri, RDFS.comment, Literal(description)))

    def serialize(self, format: str = "turtle") -> str:
        """
        Serialize the graph
        """
        return self.graph.serialize(format=format)


# Global graph object
graph: RdfGraph = RdfGraph()
