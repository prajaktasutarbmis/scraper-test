"""Generate minimal, valid, downloadable PDFs with correct xref offsets.

Two versions with DIFFERENT text so their raw bytes (and therefore the
scraper's SHA-256 content hash) differ. These are *downloaded* PDFs, hashed
raw by the portal - no HTML->PDF timestamp skipping to worry about.
"""
import sys


def escape(s):
    return s.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def build_pdf(title_lines):
    # Build a content stream: one text line per entry, dropping 20pt each line.
    y = 720
    parts = ["BT", "/F1 16 Tf"]
    first = True
    for line in title_lines:
        if first:
            parts.append(f"72 {y} Td")
            first = False
        else:
            parts.append("0 -24 Td")
        parts.append(f"({escape(line)}) Tj")
    parts.append("ET")
    stream = "\n".join(parts)
    stream_bytes = stream.encode("latin-1")

    objects = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"
    )
    objects.append(
        b"<< /Length " + str(len(stream_bytes)).encode("ascii") + b" >>\nstream\n"
        + stream_bytes + b"\nendstream"
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = bytearray()
    out += b"%PDF-1.4\n"
    out += b"%\xe2\xe3\xcf\xd3\n"  # binary marker so tools treat it as binary

    offsets = []
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += str(i).encode("ascii") + b" 0 obj\n" + body + b"\nendobj\n"

    xref_pos = len(out)
    n = len(objects) + 1
    out += b"xref\n"
    out += f"0 {n}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode("ascii")
    out += b"trailer\n"
    out += f"<< /Size {n} /Root 1 0 R >>\n".encode("ascii")
    out += b"startxref\n"
    out += f"{xref_pos}\n".encode("ascii")
    out += b"%%EOF\n"
    return bytes(out)


def main(outdir):
    v1 = build_pdf([
        "Anthem Provider Policy - TEST DOCUMENT",
        "",
        "Version 1 (original content)",
        "Policy ID: TEST-POL-0001",
        "Effective date: 2026-01-01",
        "",
        "This is a synthetic test file for scraper validation.",
        "It links from index.html and should be scraped as one file.",
    ])
    v2 = build_pdf([
        "Anthem Provider Policy - TEST DOCUMENT",
        "",
        "Version 2 (UPDATED content)",
        "Policy ID: TEST-POL-0001",
        "Effective date: 2026-06-01   <-- changed",
        "",
        "This is a synthetic test file for scraper validation.",
        "The body text changed, so the SHA-256 content hash changes too.",
        "A re-scrape should reopen this to Pending Review",
        "unless it was Strictly Rejected.",
    ])

    import os
    with open(os.path.join(outdir, "policy-v1.pdf"), "wb") as f:
        f.write(v1)
    with open(os.path.join(outdir, "policy-v2.pdf"), "wb") as f:
        f.write(v2)
    # The live file starts as v1.
    with open(os.path.join(outdir, "policy.pdf"), "wb") as f:
        f.write(v1)

    import hashlib
    print("policy-v1.pdf sha256:", hashlib.sha256(v1).hexdigest(), "bytes:", len(v1))
    print("policy-v2.pdf sha256:", hashlib.sha256(v2).hexdigest(), "bytes:", len(v2))
    print("hashes differ:", hashlib.sha256(v1).hexdigest() != hashlib.sha256(v2).hexdigest())


if __name__ == "__main__":
    main(sys.argv[1])
