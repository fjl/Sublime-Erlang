# Better Erlang Support for Sublime Text

[Sublime Text] comes with basic support for the Erlang programming language,
but most of it is just copied from TextMate and suffers from annoying bugs.
This repository contains a much-improved Erlang package.

- Hand-tuned grammar definitions for Erlang, Leex and Yecc
- *Goto Symbol* works correctly
- Snippets that *actually* make your life easier when writing Erlang code

## No IDE Functionality

This package does not provide any functionality related to
building or testing Erlang applications. If you need any of that, check out the [SublimErl] package. Compiling single files is supported.

## Installation

* clone this repository into the ST2 `Packages` folder
* remove the `Erlang` folder inside your ST2 `Packages` folder or (more elegant)
  disable the `Erlang` package in your User Settings file. 

This package is not yet available through Package Control.
I recommend tracking this repository using Package Control's "Add Repository" command.

## Contributing

The syntax files (.tmLanguage) are built from JSON sources using
[AAAPackageDev]. If you modify the grammar, please do so in the JSON file
and then generate the XML using the build system supplied by AAAPackageDev. The generated XML
files should be committed alongside your changes to the JSON.

Pull requests and issues are welcome.

[Sublime Text]: http://sublimetext.com
[SublimErl]: https://github.com/ostinelli/SublimErl
[AAAPackageDev]: https://github.com/SublimeText/AAAPackageDev
