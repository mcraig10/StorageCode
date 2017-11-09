# StorageCode
GAMS and Python scripts underlying paper on how storage affects carbon dioxide emissions from a power system as it decarbonizes. 

Paper: Craig, M.T., P. Jaramillo, and B.-M. Hodge. (In review.) Carbon dioxide emissions effects of grid-scale electricity storage in a decarbonizing power system. Environmental Research Letters. 

This directory contains data, Python code, and GAMS models. The Python code aggregates data from a variety of sources, inputs them to GAMS CE and UCED models, reads output from those models, and saves them in interpretable formats. There are also Python scripts (ResultsANalysis...) that analyze saved data from Python. The Python scripts call GAMS directly, so you will need to install the Python-GAMS API by following instructions on GAMS' website. 

Three GAMS models are included here: a capacity expansion model and 2 unit commitment and economic dispatch models (w/ and w/out storage).

This directory also contains some simple scripts that I used to run my models on the XSEDE supercomputer.

Data not included here but that must be downloaded are NREL wind and solar datasets. These datasets are from NREL's Eastern Wind Dataset and the Solar Power Data for Integration Studies datasets.
