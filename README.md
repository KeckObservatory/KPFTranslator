# KPFTranslator

# Documentation

The KPF web page at [https://www2.keck.hawaii.edu/inst/kpf/](https://www2.keck.hawaii.edu/inst/kpf/) and [https://www.keck.hawaii.edu/realpublic/inst/kpf/](https://www.keck.hawaii.edu/realpublic/inst/kpf/) is built using [mkdocs](https://www.mkdocs.org) and [mkdocstrings-python](https://mkdocstrings.github.io/python/).

To build the web page, first run the `build_docs.py` script.  This will run through the `linking_table.yml` file in the repo and generate a `.md` file under the `docs/scripts/` subdirectory which will contain the doc string for each function listed in the linking table.  It also takes the `mkdocs_input.yml` file and appends entries for those scripts to the `nav` section so that they will have a side menu entry for navigation. The only time this needs to be re-run is if the contents of `linking_table.yml` changes.  Changes to the doc strings in the scripts will get handled by the build step which is run next.

Once that script has built the `mkdocs.yml` file, run `mkdocs build` to build the HTML files in the `site/` directory.  To deploy the updated content to the Keck web site rsync those contents to the web server: `rsync -av site/* rastro@www.keck.hawaii.edu:/www/public/realpublic/inst/kpf/`.  The site is also deployed to github using `mkdocs gh-deploy` which results in a copy of the web site at [https://KeckObservatory.github.io/KPFTranslator/](https://KeckObservatory.github.io/KPFTranslator/).
