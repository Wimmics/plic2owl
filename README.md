# Plic2OWL: PlinianCore-to-OWL translation
[![License Info](http://img.shields.io/badge/license-Apache%202.0-brightgreen.svg)](LICENSE)

The [Plinian Core vocabulary](https://github.com/tdwg/PlinianCore/tree/master) is a standard data model designed to share biological species level information. It is developped as an XML schema (XSD).

The **Plinian Core ontology** is a representation the XSD PlinianCore data model as an [OWL](https://www.w3.org/TR/2012/REC-owl2-overview-20121211/) ontology, to be used in RDF-based knowledge graphs.

This repository is a Python application that transtlates the Plinian Core XML schema into an OWL ontology. The output format is [RDF Turtle](https://www.w3.org/TR/turtle/).


**WARNING**: this is an on-going work, the generated ontology may change at any time.


## Quick start guide

This repository relies on [Conda](https://conda.io/) to manage the execution environment.
File `environment.yml` defines an environment named `plic2owl`.

1) [Install Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/)
2) Set up and activate the environment:
```sh 
conda env create -f environment.yml
conda activate plic2owl
```
3) Run the translation of the currently available Plinian Core schema:

```sh
cd app
python ./main.py \
   https://raw.githubusercontent.com/tdwg/PlinianCore/master/xsd/abstract%20models/stable%20version/PlinianCore_AbstractModel_v3.2.2.7.xsd \
   --copy _schemas \
   --output ../ontology/ontology.ttl
```

## Detailed Usage

First CD to directory `app`.
Script `main.py` runs the translation. It takes a local path or a URL of the XML schema to translate, for instance:

```sh
python ./main.py /home/user/plic/PlinianCore.xsd
```
or
```sh
python ./main.py https://myserver.org/plic/PlinianCore.xsd
```

At each invocation, this will download the XML schema as well as all the imported schemas.
To save time and bandwidth, add option `--copy` to store the downloaded schemas to a local directory.

```sh
python ./main.py /home/user/plic/PlinianCore.xsd --copy _schemas
```

At subsequent invocations, the XSD files will be read from direcory `_schemas`. You may run the same command again or keep only the base name of the schema:

```sh
python ./main.py PlinianCore.xsd --copy _schemas
```

By default, the generated RDF triples are printed out on the standard output. You may change this with option `--output`:
```sh
python ./main.py PlinianCore.xsd --copy _schemas --output ../ontology/ontology.ttl
```

## Configuration

Edit file [`config/application.yml`](config/application.yml) to change the default namespace of imported XSD components (used when loaded XSDs do not mention a target namespace),
and the namespaces for which we want to generate RDF terms.

File [`config/logging.yml`](config/logging.yml) configures the application logger.
By default the target is the standard output, and the log level is WARNING. See [the logging API documentation](https://docs.python.org/3/howto/logging.html) for customization.
