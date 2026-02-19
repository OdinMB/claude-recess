"""
Quine Relay Builder: generates a Python program and a JavaScript program
such that:
  python relay_a.py  →  outputs relay_b.js
  node relay_b.js    →  outputs relay_a.py

The technique:
  Both programs carry the same data blob (base64-encoded JSON array of
  both templates). Each program decodes the blob, re-encodes it, and
  fills in the OTHER program's template with the re-encoded blob.

  Placeholder "##D##" can't appear in base64 (# isn't in the alphabet),
  so string replacement is safe.
"""

import base64
import json

# Template for the Python half. One-liner.
# The placeholder "##D##" must only appear once in each template (for the data).
# The search string for replace is constructed dynamically so the builder
# doesn't accidentally substitute it too.
T_py = 'import base64,json;d=json.loads(base64.b64decode("##D##").decode());p="##"+"D##";print(d[1].replace(p,base64.b64encode(json.dumps(d,separators=(",",":")).encode()).decode()))'

# Template for the JavaScript half. One-liner.
T_js = 'd=JSON.parse(Buffer.from("##D##","base64").toString());p="##"+"D##";process.stdout.write(d[0].replace(p,Buffer.from(JSON.stringify(d)).toString("base64"))+"\\n")'

# Build the data blob: JSON array of both templates, base64-encoded
data_json = json.dumps([T_py, T_js], separators=(',', ':'))
data_b64 = base64.b64encode(data_json.encode()).decode()

# Fill in each template
py_program = T_py.replace("##D##", data_b64)
js_program = T_js.replace("##D##", data_b64)

# Write output files
with open("relay_a.py", "w", newline='\n') as f:
    f.write(py_program + "\n")

with open("relay_b.js", "w", newline='\n') as f:
    f.write(js_program + "\n")

print(f"Data blob size: {len(data_b64)} chars")
print(f"relay_a.py: {len(py_program)} chars")
print(f"relay_b.js: {len(js_program)} chars")
print()
print("Test with:")
print("  python relay_a.py > test_b.js")
print("  node test_b.js > test_a.py")
print("  diff relay_a.py test_a.py")
