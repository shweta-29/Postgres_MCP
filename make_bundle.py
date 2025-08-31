# make_bundle.py
import certifi, pathlib
corp = pathlib.Path(r"C:\certs\corp-root.pem")
bundle = pathlib.Path(r"C:\certs\corp-bundle.pem")
bundle.write_bytes(corp.read_bytes() + pathlib.Path(certifi.where()).read_bytes())
print(bundle)
