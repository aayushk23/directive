from pathlib import Path


def write_readable_pdf(source_file: Path, lines: list[str]) -> None:
    text_commands = "\n".join(f"({_escape_pdf_text(line)}) Tj T*" for line in lines)
    content_stream = (f"BT\n/F1 12 Tf\n72 720 Td\n14 TL\n{text_commands}\nET\n").encode(
        "latin-1"
    )

    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        (
            f"<< /Length {len(content_stream)} >>\n".encode("latin-1")
            + b"stream\n"
            + content_stream
            + b"endstream"
        ),
    ]

    pdf_parts = [b"%PDF-1.4\n"]
    offsets = [0]
    current_offset = len(pdf_parts[0])

    for index, pdf_object in enumerate(objects, start=1):
        offsets.append(current_offset)
        object_bytes = f"{index} 0 obj\n".encode("latin-1") + pdf_object + b"\nendobj\n"
        pdf_parts.append(object_bytes)
        current_offset += len(object_bytes)

    xref_offset = current_offset
    xref_lines = ["xref", "0 6", "0000000000 65535 f "]
    xref_lines.extend(f"{offset:010d} 00000 n " for offset in offsets[1:])
    xref = "\n".join(xref_lines).encode("latin-1") + b"\n"
    trailer = (
        b"trailer\n"
        b"<< /Size 6 /Root 1 0 R >>\n"
        b"startxref\n" + str(xref_offset).encode("latin-1") + b"\n%%EOF\n"
    )

    source_file.write_bytes(b"".join(pdf_parts) + xref + trailer)


def _escape_pdf_text(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
