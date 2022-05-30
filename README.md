# RayScanner

Simple package to make a random scan on a parameter space of a BSM physics model with SPheno, HiggsBounds and HiggsSignals. The parameters to scan are defined in the `hep_tools.yaml` file along with the parameter regions. The final data is saved in the data.csv file.

It uses Ray to run in parallel (embarrassingly parallel) with cores specified in the hep_tools.yaml file too. It is originaly created to run in Iridis5, with the submit file. But you can just run it locally with run_scan.py.

It has a data visualizer created with Streamlit. To run it locally run: 

`streamlit run --server.port 8080 visualizer.py`

Also you can see the visualizer in this link: [visualizer](https://share.streamlit.io/mjadiaz/ray-hep-scanner/visualizer.py)
