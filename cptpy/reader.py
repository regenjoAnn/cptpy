"""Readers for common vendor CPT file formats."""

import numpy as np

from .cpt import CPT
from .cptu import CPTu

__all__ = ["read_cpt"]


def _parse_kv_line(line):
    """Parse a ``key=value,key=value`` line into a dict of strings."""
    record = {}
    for token in line.split(","):
        key, sep, value = token.partition("=")
        if sep:
            record[key.strip()] = value.strip()
    return record


def read_cpt(fname, qc_in_mpa=True, encoding="latin-1"):
    """Read a column-style vendor ``.cpt`` file (e.g., Vertek/Hogentogler).

    These files contain a metadata header (lines beginning with ``H``)
    followed by per-depth data rows of the form::

        D=0.000,QC=0.7520,FS=3.5,U=19.4,TA=0.28,B=0,...

    where ``D`` is depth in metres, ``QC`` is cone tip resistance,
    ``FS`` is sleeve friction in kPa, and ``U`` (when present) is pore
    water pressure in kPa. Any trailing event/alarm log lines are
    ignored.

    Parameters
    ----------
    fname : str
        Path to the ``.cpt`` file.
    qc_in_mpa : bool, optional
        If ``True`` (the default) the ``QC`` column is assumed to be in
        MPa and is converted to kPa. Set to ``False`` if ``QC`` is
        already in kPa.
    encoding : str, optional
        Text encoding of the file, default is ``"latin-1"`` which safely
        decodes the extended characters (e.g., degree symbols) found in
        these files.

    Returns
    -------
    CPT or CPTu
        A :class:`~cptpy.cptu.CPTu` when a pore-pressure (``U``) column
        is present, otherwise a :class:`~cptpy.cpt.CPT`. The parsed
        header metadata is attached as a ``.metadata`` dict.

    """
    header = {}
    depth, qc, fs, u2 = [], [], [], []

    with open(fname, encoding=encoding) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("D="):
                record = _parse_kv_line(line)
                depth.append(float(record["D"]))
                qc.append(float(record["QC"]))
                fs.append(float(record["FS"]))
                if "U" in record:
                    u2.append(float(record["U"]))
            elif line[:1] == "H":
                # Metadata header line (HA=1,HB=4,...).
                header.update(_parse_kv_line(line))

    if not depth:
        raise ValueError(f"No 'D=' data rows found in {fname!r}; is this a "
                         "column-style vendor .cpt file?")

    qc_to_kpa = (lambda qc: qc * 1000.0) if qc_in_mpa else (lambda qc: qc)

    has_u2 = len(u2) == len(depth)
    if has_u2:
        obj = CPTu(depth, qc, fs, u2, qc_to_kpa=qc_to_kpa)
    else:
        obj = CPT(depth, qc, fs, qc_to_kpa=qc_to_kpa)

    obj.metadata = header
    return obj
