"""
Offline Evidence Verification Agent.

This module performs conservative local checks for compliance evidence files.
It never approves missing files, unsupported formats, malformed containers, or
files with structural tamper indicators.
"""

import base64
import binascii
import io
import os
import re
import struct
import zipfile
import zlib
from datetime import datetime
from xml.etree import ElementTree


ALLOWED_TYPES = {"pdf", "png", "jpg", "docx"}
SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".png": "png",
    ".jpg": "jpg",
    ".jpeg": "jpg",
    ".docx": "docx",
}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
ZIP_SIGNATURES = (b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")
EDITOR_MARKERS = (
    "adobe photoshop",
    "photoshop",
    "gimp",
    "paint.net",
    "canva",
    "pixlr",
    "snapseed",
    "exiftool",
)
EVIDENCE_STOP_WORDS = {
    "and",
    "for",
    "the",
    "with",
    "from",
    "this",
    "that",
    "proof",
    "evidence",
    "required",
    "compliance",
    "review",
    "sample",
}


def _utc_now():
    return datetime.utcnow().isoformat()


def _empty_checks():
    return {
        "file_exists": False,
        "allowed_type": False,
        "metadata_consistent": False,
        "tamper_indicators_found": False,
        "content_matches_required_evidence": False,
    }


def _finding(severity, location, reason, suggested_action, page=1):
    return {
        "severity": severity,
        "page": page,
        "location": location,
        "reason": reason,
        "suggested_action": suggested_action,
    }


def _response(
    status,
    tampered,
    risk_score,
    confidence,
    file_type,
    summary,
    findings,
    checks,
):
    return {
        "status": status,
        "tampered": bool(tampered),
        "risk_score": max(0, min(100, int(risk_score))),
        "confidence": max(0, min(1, round(float(confidence), 2))),
        "file_type": file_type if file_type in ALLOWED_TYPES else "unknown",
        "summary": summary,
        "findings": findings,
        "checks": checks,
        "verified_at": _utc_now(),
        "engine": "offline_evidence_verifier",
    }


def _reject(summary, reason, file_type="unknown", checks=None, location="file header"):
    return _response(
        status="REJECTED",
        tampered=False,
        risk_score=100,
        confidence=1,
        file_type=file_type,
        summary=summary,
        findings=[
            _finding(
                "High",
                location,
                reason,
                "Upload a valid PDF, PNG, JPG/JPEG, or DOCX evidence file.",
            )
        ],
        checks=checks or _empty_checks(),
    )


def _extension_type(filename):
    _, extension = os.path.splitext(filename or "")
    return SUPPORTED_EXTENSIONS.get(extension.lower())


def _file_extension(filename):
    _, extension = os.path.splitext(filename or "")
    return extension.lower()


def _magic_type(data):
    if data.startswith(b"%PDF-"):
        return "pdf"
    if data.startswith(PNG_SIGNATURE):
        return "png"
    if data.startswith(b"\xff\xd8"):
        return "jpg"
    if data.startswith(ZIP_SIGNATURES):
        return "docx"
    return None


def _contains_editor_marker(raw_text):
    lower_text = raw_text.lower()
    return next((marker for marker in EDITOR_MARKERS if marker in lower_text), None)


def _extract_printable_text(data, max_bytes=250000):
    text = data[:max_bytes].decode("latin-1", errors="ignore")
    return " ".join(re.findall(r"[A-Za-z0-9][A-Za-z0-9 /_.:-]{2,}", text))


def _evidence_tokens(required_evidence):
    if not required_evidence:
        return []

    tokens = re.findall(r"[a-z0-9]{4,}", required_evidence.lower())
    return [
        token
        for token in tokens
        if token not in EVIDENCE_STOP_WORDS and not token.isdigit()
    ][:12]


def _content_matches_required_evidence(required_evidence, extracted_text, filename):
    tokens = _evidence_tokens(required_evidence)
    if not tokens:
        return True

    haystack = f"{filename or ''} {extracted_text or ''}".lower()
    matched = [token for token in tokens if token in haystack]
    required_matches = 1 if len(tokens) <= 2 else min(3, max(2, len(tokens) // 3))
    return len(matched) >= required_matches


def _validate_pdf(data):
    findings = []
    extracted_text = _extract_printable_text(data)

    if not data.startswith(b"%PDF-"):
        return {
            "malformed": True,
            "tampered": False,
            "metadata_consistent": False,
            "extracted_text": extracted_text,
            "summary": "PDF evidence rejected because the PDF header is missing.",
            "findings": [
                _finding(
                    "High",
                    "file header",
                    "The file does not begin with a valid %PDF header.",
                    "Upload an original PDF export.",
                )
            ],
        }

    if b"%%EOF" not in data[-4096:]:
        return {
            "malformed": True,
            "tampered": False,
            "metadata_consistent": False,
            "extracted_text": extracted_text,
            "summary": "PDF evidence rejected because the PDF footer is missing.",
            "findings": [
                _finding(
                    "High",
                    "file header",
                    "The file is missing a valid %%EOF marker near the end of the document.",
                    "Regenerate the PDF and upload the unmodified export.",
                )
            ],
        }

    lower_text = extracted_text.lower()
    tampered = False
    metadata_consistent = True

    if data.count(b"%%EOF") > 1 or b"/Prev" in data:
        tampered = True
        metadata_consistent = False
        findings.append(
            _finding(
                "Medium",
                "metadata",
                "The PDF contains incremental update markers, which can indicate post-generation editing.",
                "Review the source system export and confirm the latest revision history.",
            )
        )

    editor_marker = _contains_editor_marker(lower_text)
    if editor_marker:
        tampered = True
        metadata_consistent = False
        findings.append(
            _finding(
                "High",
                "metadata",
                f"The PDF metadata references an editing tool: {editor_marker}.",
                "Request a fresh system-generated PDF without manual editing.",
            )
        )

    if any(marker in lower_text for marker in ["/javascript", "/openaction", "/embeddedfile"]):
        tampered = True
        metadata_consistent = False
        findings.append(
            _finding(
                "High",
                "metadata",
                "The PDF contains active-content or embedded-file markers.",
                "Manually review the PDF in a safe viewer before accepting it as evidence.",
            )
        )

    if b"startxref" not in data[-8192:]:
        metadata_consistent = False
        findings.append(
            _finding(
                "Medium",
                "file header",
                "The PDF has no startxref marker near the end of the file.",
                "Regenerate the PDF from the source system if possible.",
            )
        )

    return {
        "malformed": False,
        "tampered": tampered,
        "metadata_consistent": metadata_consistent,
        "extracted_text": extracted_text,
        "summary": "PDF structure is readable; no blocking corruption was detected.",
        "findings": findings,
    }


def _validate_png(data):
    findings = []
    extracted_text_parts = []

    if not data.startswith(PNG_SIGNATURE):
        return {
            "malformed": True,
            "tampered": False,
            "metadata_consistent": False,
            "extracted_text": "",
            "summary": "PNG evidence rejected because the PNG signature is invalid.",
            "findings": [
                _finding(
                    "High",
                    "file header",
                    "The file does not start with a valid PNG signature.",
                    "Upload a valid PNG screenshot or export.",
                )
            ],
        }

    offset = len(PNG_SIGNATURE)
    saw_ihdr = False
    saw_iend = False
    iend_offset = None
    metadata_consistent = True
    tampered = False
    width = 0
    height = 0

    while offset < len(data):
        if offset + 8 > len(data):
            return {
                "malformed": True,
                "tampered": False,
                "metadata_consistent": False,
                "extracted_text": " ".join(extracted_text_parts),
                "summary": "PNG evidence rejected because a chunk header is incomplete.",
                "findings": [
                    _finding(
                        "High",
                        "file header",
                        "The PNG chunk table ends unexpectedly.",
                        "Export the PNG again and upload the complete file.",
                    )
                ],
            }

        chunk_length = struct.unpack(">I", data[offset : offset + 4])[0]
        chunk_type = data[offset + 4 : offset + 8]
        chunk_start = offset + 8
        chunk_end = chunk_start + chunk_length
        crc_end = chunk_end + 4

        if crc_end > len(data):
            return {
                "malformed": True,
                "tampered": False,
                "metadata_consistent": False,
                "extracted_text": " ".join(extracted_text_parts),
                "summary": "PNG evidence rejected because a chunk length is invalid.",
                "findings": [
                    _finding(
                        "High",
                        "file header",
                        f"Chunk {chunk_type.decode('latin-1', errors='ignore')} exceeds file length.",
                        "Upload a non-corrupted PNG file.",
                    )
                ],
            }

        chunk_data = data[chunk_start:chunk_end]
        expected_crc = struct.unpack(">I", data[chunk_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF

        if expected_crc != actual_crc:
            return {
                "malformed": True,
                "tampered": False,
                "metadata_consistent": False,
                "extracted_text": " ".join(extracted_text_parts),
                "summary": "PNG evidence rejected because checksum validation failed.",
                "findings": [
                    _finding(
                        "High",
                        "file header",
                        f"Chunk {chunk_type.decode('latin-1', errors='ignore')} has an invalid CRC.",
                        "Upload the original PNG export without manual modification.",
                    )
                ],
            }

        if not saw_ihdr and chunk_type != b"IHDR":
            return {
                "malformed": True,
                "tampered": False,
                "metadata_consistent": False,
                "extracted_text": " ".join(extracted_text_parts),
                "summary": "PNG evidence rejected because IHDR is not the first chunk.",
                "findings": [
                    _finding(
                        "High",
                        "file header",
                        "A valid PNG must start its chunk stream with IHDR.",
                        "Upload a valid PNG screenshot or export.",
                    )
                ],
            }

        if chunk_type == b"IHDR":
            saw_ihdr = True
            width, height = struct.unpack(">II", chunk_data[:8])
            if width == 0 or height == 0:
                return {
                    "malformed": True,
                    "tampered": False,
                    "metadata_consistent": False,
                    "extracted_text": " ".join(extracted_text_parts),
                    "summary": "PNG evidence rejected because image dimensions are invalid.",
                    "findings": [
                        _finding(
                            "High",
                            "visual region",
                            "The PNG reports zero width or height.",
                            "Upload a real screenshot or exported evidence image.",
                        )
                    ],
                }

            if width < 400 or height < 250:
                findings.append(
                    _finding(
                        "Low",
                        "visual region",
                        f"The PNG resolution is small for audit evidence: {width}x{height}.",
                        "Confirm the file shows the complete evidence screen.",
                    )
                )

        if chunk_type in {b"tEXt", b"iTXt", b"zTXt"}:
            metadata_text = chunk_data.decode("latin-1", errors="ignore")
            extracted_text_parts.append(metadata_text)
            editor_marker = _contains_editor_marker(metadata_text)
            if editor_marker:
                tampered = True
                metadata_consistent = False
                findings.append(
                    _finding(
                        "High",
                        "metadata",
                        f"PNG metadata references an editing tool: {editor_marker}.",
                        "Request a fresh screenshot or export directly from the source system.",
                    )
                )

        if chunk_type == b"IEND":
            saw_iend = True
            iend_offset = crc_end
            break

        offset = crc_end

    if not saw_iend:
        return {
            "malformed": True,
            "tampered": False,
            "metadata_consistent": False,
            "extracted_text": " ".join(extracted_text_parts),
            "summary": "PNG evidence rejected because the IEND chunk is missing.",
            "findings": [
                _finding(
                    "High",
                    "file header",
                    "The PNG does not contain a valid IEND chunk.",
                    "Upload the complete original PNG file.",
                )
            ],
        }

    trailing_bytes = data[iend_offset:].strip(b"\x00\r\n\t ")
    if trailing_bytes:
        tampered = True
        metadata_consistent = False
        findings.append(
            _finding(
                "Medium",
                "file header",
                "Unexpected bytes were found after the PNG IEND chunk.",
                "Review the evidence manually and request a clean export if needed.",
            )
        )

    return {
        "malformed": False,
        "tampered": tampered,
        "metadata_consistent": metadata_consistent,
        "extracted_text": " ".join(extracted_text_parts),
        "summary": f"PNG structure is readable at {width}x{height}.",
        "findings": findings,
    }


def _validate_jpg(data):
    findings = []
    extracted_text_parts = []

    if not data.startswith(b"\xff\xd8"):
        return {
            "malformed": True,
            "tampered": False,
            "metadata_consistent": False,
            "extracted_text": "",
            "summary": "JPG evidence rejected because the JPEG header is invalid.",
            "findings": [
                _finding(
                    "High",
                    "file header",
                    "The file does not start with a JPEG SOI marker.",
                    "Upload a valid JPG/JPEG file.",
                )
            ],
        }

    eoi_index = data.rfind(b"\xff\xd9")
    if eoi_index == -1:
        return {
            "malformed": True,
            "tampered": False,
            "metadata_consistent": False,
            "extracted_text": "",
            "summary": "JPG evidence rejected because the JPEG footer is missing.",
            "findings": [
                _finding(
                    "High",
                    "file header",
                    "The file has no JPEG EOI marker.",
                    "Upload a complete, non-corrupted JPG/JPEG file.",
                )
            ],
        }

    tampered = False
    metadata_consistent = True
    width = 0
    height = 0
    saw_scan = False
    offset = 2

    while offset < eoi_index:
        if data[offset] != 0xFF:
            if saw_scan:
                break
            return {
                "malformed": True,
                "tampered": False,
                "metadata_consistent": False,
                "extracted_text": " ".join(extracted_text_parts),
                "summary": "JPG evidence rejected because segment markers are invalid.",
                "findings": [
                    _finding(
                        "High",
                        "file header",
                        "The JPEG segment stream is malformed before image data begins.",
                        "Upload a fresh JPG/JPEG export.",
                    )
                ],
            }

        while offset < eoi_index and data[offset] == 0xFF:
            offset += 1

        if offset >= eoi_index:
            break

        marker = data[offset]
        offset += 1

        if marker in {0x00, 0x01} or 0xD0 <= marker <= 0xD9:
            continue

        if offset + 2 > len(data):
            return {
                "malformed": True,
                "tampered": False,
                "metadata_consistent": False,
                "extracted_text": " ".join(extracted_text_parts),
                "summary": "JPG evidence rejected because a segment length is missing.",
                "findings": [
                    _finding(
                        "High",
                        "file header",
                        "A JPEG segment is truncated.",
                        "Upload a complete JPG/JPEG file.",
                    )
                ],
            }

        segment_length = struct.unpack(">H", data[offset : offset + 2])[0]
        if segment_length < 2:
            return {
                "malformed": True,
                "tampered": False,
                "metadata_consistent": False,
                "extracted_text": " ".join(extracted_text_parts),
                "summary": "JPG evidence rejected because a segment length is invalid.",
                "findings": [
                    _finding(
                        "High",
                        "file header",
                        "A JPEG segment has an impossible length.",
                        "Upload a valid JPG/JPEG file.",
                    )
                ],
            }

        segment_start = offset + 2
        segment_end = segment_start + segment_length - 2
        if segment_end > len(data):
            return {
                "malformed": True,
                "tampered": False,
                "metadata_consistent": False,
                "extracted_text": " ".join(extracted_text_parts),
                "summary": "JPG evidence rejected because a segment exceeds file length.",
                "findings": [
                    _finding(
                        "High",
                        "file header",
                        "The JPEG segment table points beyond the uploaded file.",
                        "Upload a non-corrupted JPG/JPEG file.",
                    )
                ],
            }

        segment = data[segment_start:segment_end]
        segment_text = segment.decode("latin-1", errors="ignore")
        extracted_text_parts.append(segment_text)

        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}:
            if len(segment) >= 5:
                height, width = struct.unpack(">HH", segment[1:5])
                if width < 400 or height < 250:
                    findings.append(
                        _finding(
                            "Low",
                            "visual region",
                            f"The JPG resolution is small for audit evidence: {width}x{height}.",
                            "Confirm the file shows the complete evidence screen.",
                        )
                    )

        editor_marker = _contains_editor_marker(segment_text)
        if editor_marker or marker == 0xED:
            tampered = True
            metadata_consistent = False
            reason = (
                f"JPG metadata references an editing tool: {editor_marker}."
                if editor_marker
                else "The JPG contains a Photoshop APP13 metadata segment."
            )
            findings.append(
                _finding(
                    "High",
                    "metadata",
                    reason,
                    "Request a fresh screenshot or export directly from the source system.",
                )
            )

        offset = segment_end

        if marker == 0xDA:
            saw_scan = True
            break

    trailing_bytes = data[eoi_index + 2 :].strip(b"\x00\r\n\t ")
    if trailing_bytes:
        tampered = True
        metadata_consistent = False
        findings.append(
            _finding(
                "Medium",
                "file header",
                "Unexpected bytes were found after the JPEG EOI marker.",
                "Review the evidence manually and request a clean export if needed.",
            )
        )

    if not saw_scan or width == 0 or height == 0:
        metadata_consistent = False
        findings.append(
            _finding(
                "Medium",
                "file header",
                "The JPEG is readable but lacks expected scan or dimension metadata.",
                "Manually review the image before accepting it.",
            )
        )

    return {
        "malformed": False,
        "tampered": tampered,
        "metadata_consistent": metadata_consistent,
        "extracted_text": " ".join(extracted_text_parts),
        "summary": f"JPG structure is readable at {width or 'unknown'}x{height or 'unknown'}.",
        "findings": findings,
    }


def _extract_docx_text(document_xml):
    try:
        root = ElementTree.fromstring(document_xml)
    except ElementTree.ParseError:
        return ""

    text_parts = []
    for element in root.iter():
        if element.tag.endswith("}t") and element.text:
            text_parts.append(element.text)
    return " ".join(text_parts)


def _validate_docx(data):
    findings = []
    extracted_text = ""
    tampered = False
    metadata_consistent = True

    try:
        with zipfile.ZipFile(io.BytesIO(data)) as docx:
            bad_member = docx.testzip()
            if bad_member:
                return {
                    "malformed": True,
                    "tampered": False,
                    "metadata_consistent": False,
                    "extracted_text": "",
                    "summary": "DOCX evidence rejected because ZIP integrity validation failed.",
                    "findings": [
                        _finding(
                            "High",
                            "file header",
                            f"DOCX ZIP member failed CRC validation: {bad_member}.",
                            "Upload a non-corrupted DOCX file.",
                        )
                    ],
                }

            names = set(docx.namelist())
            required_members = {"[Content_Types].xml", "word/document.xml"}
            missing_members = sorted(required_members - names)
            if missing_members:
                return {
                    "malformed": True,
                    "tampered": False,
                    "metadata_consistent": False,
                    "extracted_text": "",
                    "summary": "DOCX evidence rejected because required document parts are missing.",
                    "findings": [
                        _finding(
                            "High",
                            "file header",
                            f"Missing required DOCX members: {', '.join(missing_members)}.",
                            "Upload a valid DOCX generated by a trusted editor or source system.",
                        )
                    ],
                }

            document_xml = docx.read("word/document.xml")
            extracted_text = _extract_docx_text(document_xml)
            document_xml_text = document_xml.decode("utf-8", errors="ignore").lower()

            if any(name.lower().endswith("vbaproject.bin") for name in names):
                tampered = True
                metadata_consistent = False
                findings.append(
                    _finding(
                        "High",
                        "metadata",
                        "The DOCX package contains macro project content.",
                        "Reject macro-enabled evidence or request a clean DOCX/PDF export.",
                    )
                )

            if "<w:ins" in document_xml_text or "<w:del" in document_xml_text:
                tampered = True
                metadata_consistent = False
                findings.append(
                    _finding(
                        "Medium",
                        "document text",
                        "The DOCX contains tracked insertions or deletions.",
                        "Review the document history and request a finalized clean copy.",
                    )
                )

            if "word/comments.xml" in names:
                tampered = True
                metadata_consistent = False
                findings.append(
                    _finding(
                        "Medium",
                        "document text",
                        "The DOCX contains comments, which may indicate review edits.",
                        "Confirm comments do not alter the submitted evidence.",
                    )
                )

            if "docProps/core.xml" in names:
                core_text = docx.read("docProps/core.xml").decode("utf-8", errors="ignore")
                editor_marker = _contains_editor_marker(core_text)
                if editor_marker:
                    tampered = True
                    metadata_consistent = False
                    findings.append(
                        _finding(
                            "High",
                            "metadata",
                            f"DOCX metadata references an editing tool: {editor_marker}.",
                            "Request a fresh document export from the source system.",
                        )
                    )

            if not extracted_text.strip():
                metadata_consistent = False
                findings.append(
                    _finding(
                        "Medium",
                        "document text",
                        "The DOCX contains no extractable text.",
                        "Manually confirm the document contains the expected evidence.",
                    )
                )
    except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
        return {
            "malformed": True,
            "tampered": False,
            "metadata_consistent": False,
            "extracted_text": "",
            "summary": "DOCX evidence rejected because the document package is malformed.",
            "findings": [
                _finding(
                    "High",
                    "file header",
                    f"DOCX package could not be opened: {exc}.",
                    "Upload a valid DOCX file.",
                )
            ],
        }

    return {
        "malformed": False,
        "tampered": tampered,
        "metadata_consistent": metadata_consistent,
        "extracted_text": extracted_text,
        "summary": "DOCX package is readable and required document parts are present.",
        "findings": findings,
    }


VALIDATORS = {
    "pdf": _validate_pdf,
    "png": _validate_png,
    "jpg": _validate_jpg,
    "docx": _validate_docx,
}


def _score_result(tampered, metadata_consistent, content_matches, findings):
    if tampered:
        return 78, 0.62
    if not metadata_consistent:
        return 52, 0.68
    if not content_matches:
        return 35, 0.72
    if findings:
        return 18, 0.86
    return 8, 0.94


def verify_evidence_bytes(
    file_bytes=None,
    filename=None,
    content_type=None,
    required_evidence=None,
):
    """Verify uploaded evidence bytes and return the Member D evidence schema."""
    del content_type  # Content type is supplied by the browser and is not trusted.

    checks = _empty_checks()

    if not file_bytes:
        return _reject(
            summary="Evidence rejected: no file was provided.",
            reason="No evidence file was uploaded for verification.",
            checks=checks,
            location="file header",
        )

    checks["file_exists"] = True
    filename = filename or "uploaded_evidence"
    raw_extension = _file_extension(filename)
    extension_type = _extension_type(filename)
    magic_type = _magic_type(file_bytes)

    if raw_extension and extension_type is None:
        return _reject(
            summary="Evidence rejected: unsupported filename extension.",
            reason=f"The extension {raw_extension} is not supported for evidence verification.",
            file_type=magic_type or "unknown",
            checks=checks,
            location="file header",
        )

    if extension_type is None and magic_type is None:
        return _reject(
            summary="Evidence rejected: unsupported file type.",
            reason="The file is not a supported PDF, PNG, JPG/JPEG, or DOCX.",
            checks=checks,
            location="file header",
        )

    if extension_type is None and magic_type in ALLOWED_TYPES:
        file_type = magic_type
        checks["allowed_type"] = True
        extension_finding = _finding(
            "Medium",
            "file header",
            "The file content is supported, but the filename extension is missing or unsupported.",
            "Rename or export the evidence with the correct extension before final acceptance.",
        )
    elif extension_type in ALLOWED_TYPES and magic_type is None:
        file_type = extension_type
        checks["allowed_type"] = True
        validation_checks = checks.copy()
        validation_checks["metadata_consistent"] = False
        return _reject(
            summary="Evidence rejected: file content does not match the declared type.",
            reason=f"The filename suggests {extension_type.upper()}, but the file header is not valid.",
            file_type=file_type,
            checks=validation_checks,
            location="file header",
        )
    elif extension_type != magic_type:
        file_type = extension_type or magic_type or "unknown"
        checks["allowed_type"] = extension_type in ALLOWED_TYPES and magic_type in ALLOWED_TYPES
        validation_checks = checks.copy()
        validation_checks["metadata_consistent"] = False
        return _reject(
            summary="Evidence rejected: filename extension and file header do not match.",
            reason=f"Declared type is {extension_type or 'unknown'}, but header indicates {magic_type or 'unknown'}.",
            file_type=file_type,
            checks=validation_checks,
            location="file header",
        )
    else:
        file_type = extension_type
        checks["allowed_type"] = True
        extension_finding = None

    validator = VALIDATORS.get(file_type)
    validation = validator(file_bytes)
    findings = list(validation["findings"])

    if extension_finding:
        findings.insert(0, extension_finding)

    if validation["malformed"]:
        checks["metadata_consistent"] = False
        return _response(
            status="REJECTED",
            tampered=False,
            risk_score=96,
            confidence=0.98,
            file_type=file_type,
            summary=validation["summary"],
            findings=findings,
            checks=checks,
        )

    content_matches = _content_matches_required_evidence(
        required_evidence,
        validation["extracted_text"],
        filename,
    )
    metadata_consistent = bool(validation["metadata_consistent"]) and not extension_finding
    tampered = bool(validation["tampered"])

    checks["metadata_consistent"] = metadata_consistent
    checks["tamper_indicators_found"] = tampered
    checks["content_matches_required_evidence"] = content_matches

    if not content_matches:
        findings.append(
            _finding(
                "Low",
                "document text" if file_type in {"pdf", "docx"} else "visual region",
                "The verifier could not confidently match the file content to the required evidence description.",
                "Have the branch custodian manually confirm this file satisfies the selected MAP proof requirement.",
            )
        )

    if not findings:
        findings.append(
            _finding(
                "Low",
                "file header",
                "File structure and metadata checks did not reveal tamper indicators.",
                "Retain the evidence with the compliance action record.",
            )
        )

    risk_score, confidence = _score_result(
        tampered=tampered,
        metadata_consistent=metadata_consistent,
        content_matches=content_matches,
        findings=findings,
    )

    if tampered:
        status = "NEEDS_REVIEW"
        summary = (
            f"{file_type.upper()} evidence needs manual review because tamper "
            "or editing indicators were found."
        )
    elif not metadata_consistent:
        status = "NEEDS_REVIEW"
        summary = (
            f"{file_type.upper()} evidence needs manual review because metadata "
            "or structural expectations are incomplete."
        )
    elif not content_matches:
        status = "NEEDS_REVIEW"
        summary = (
            f"{file_type.upper()} evidence is structurally valid, but content "
            "match requires branch custodian review."
        )
    else:
        status = "APPROVED"
        summary = (
            f"{file_type.upper()} evidence approved by offline structural, "
            "metadata, and requirement-match checks."
        )

    return _response(
        status=status,
        tampered=tampered,
        risk_score=risk_score,
        confidence=confidence,
        file_type=file_type,
        summary=summary,
        findings=findings,
        checks=checks,
    )


def verify_evidence_file(image_path=None, required_evidence=None):
    """Verify an evidence file from a local path."""
    checks = _empty_checks()

    if not image_path:
        return _reject(
            summary="Evidence rejected: no file path was provided.",
            reason="No evidence file path was supplied for verification.",
            checks=checks,
        )

    if not os.path.isfile(image_path):
        return _reject(
            summary="Evidence rejected: file path does not exist.",
            reason=f"The evidence file was not found: {image_path}.",
            checks=checks,
        )

    try:
        with open(image_path, "rb") as file_handle:
            file_bytes = file_handle.read()
    except OSError as exc:
        checks["file_exists"] = True
        return _reject(
            summary="Evidence rejected: file could not be read.",
            reason=f"The evidence file exists but could not be opened: {exc}.",
            checks=checks,
        )

    return verify_evidence_bytes(
        file_bytes=file_bytes,
        filename=os.path.basename(image_path),
        required_evidence=required_evidence,
    )


def verify_evidence_image(image_path=None, image_base64=None, required_evidence=None):
    """
    Backward-compatible entrypoint for older image verification callers.
    Returns the new conservative evidence verification schema.
    """
    if image_path:
        return verify_evidence_file(
            image_path=image_path,
            required_evidence=required_evidence,
        )

    if not image_base64:
        return verify_evidence_bytes(
            file_bytes=None,
            filename="uploaded_evidence",
            required_evidence=required_evidence,
        )

    try:
        file_bytes = base64.b64decode(image_base64, validate=True)
    except (binascii.Error, ValueError):
        return _reject(
            summary="Evidence rejected: base64 image payload is malformed.",
            reason="The uploaded image payload could not be decoded.",
            checks=_empty_checks(),
        )

    return verify_evidence_bytes(
        file_bytes=file_bytes,
        filename="uploaded_evidence",
        required_evidence=required_evidence,
    )


def verify_evidence_from_upload(
    file_bytes=None,
    filename=None,
    content_type=None,
    required_evidence=None,
):
    """Verify evidence from raw upload bytes for the FastAPI endpoint."""
    return verify_evidence_bytes(
        file_bytes=file_bytes,
        filename=filename,
        content_type=content_type,
        required_evidence=required_evidence,
    )


if __name__ == "__main__":
    print(verify_evidence_file(image_path="nonexistent.png"))
