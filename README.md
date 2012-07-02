# Better Erlang Support for Sublime Text 2

Sublime Text 2 comes with basic support for the Erlang programming language,
but most of it is just copied from TextMate and suffers from some pretty annoying bugs.
This repository is an attempt to rectify that situation, providing fixes
for the issues that bug me most.

# Installation

* clone this repository into the ST2 `Packages` folder
* remove the `Erlang` folder inside your ST2 `Packages` folder or (more elegant)
  disable the `Erlang` package in your User Settings file. 

I'd recommend tracking this repository using Package Control's "Add Repository" command.

# Contributing

The syntax files (.tmLanguage) are generated from JSON source using
[AAAPackageDev](https://github.com/SublimeText/AAAPackageDev). If you
modify the grammar, please do so in the JSON file and then generate the XML
using the build system supplied by AAAPackageDev. The generated XML
files should be committed alongside your changes to the JSON.

Pull requests and issues are welcome.
