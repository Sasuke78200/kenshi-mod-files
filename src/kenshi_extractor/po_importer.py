import polib

from pathlib import Path

from mod_file import ModFile


def import_po(mod_file: ModFile, po_file: Path | str) -> None:
    """ Mutate in place the `ModFile` with translated strings from `po_file` """
    po = polib.pofile(po_file)

    # extract the translated fields into a dict
    translated_fields = {entry.msgctxt: entry.msgstr for entry in po.translated_entries()}

    if 'header::description' in translated_fields:
        mod_file.header.description = translated_fields['header::description']

    for item in mod_file.items:
        for k in item.fields.strings:
            msgctxt = f'{item.identifier}::{item.item_type.name}::{k}'
            if msgctxt in translated_fields:
                item.fields.strings[k] = translated_fields[msgctxt]
