

from pylibdmtx import pylibdmtx
encoded = pylibdmtx.encode(b"Test")
print("Data Matrix generated:", len(encoded.pixels))

