import polib

from mod_file import ModFile
from mod_item import ModItem, ItemType


TRANSLATABLE_FIELDS = (
    'Description',          # Capitalized version
    'description',          # lower version, that's like this on the FCS code
    'building category',
    'building group',
    'category',
    'inventory content name',
    'building name',
    'string',
    'company description',
    'unexplored name',
    'display name',
    'difficulty',
    'style',
    'stats affected',
    'ways to train',
    'layout interior', # not in list, but found in code `TranslationManager::BuildCoreMessages`
)

def _field_is_translatable(item: ModItem, field_name: str):
    if field_name in TRANSLATABLE_FIELDS:
        return True
    if item.item_type == ItemType.DIALOGUE_LINE and field_name.startswith(('text', '-', '_')):   # Could match text_size, textXXXX, but it seems like that's how it is done on FCS
        return True
    return False


def _item_is_translatable(item: ModItem) -> bool:
    return any(_field_is_translatable(item, str_field) for str_field in item.fields.strings)


def export_po(mod_file: ModFile) -> polib.POFile:
    po = polib.POFile()
    po.metadata = {
        'Content-Type': 'text/plain; charset=utf-8',
        'Content-Transfer-Encoding': '8bit',
        'X-Generator': 'kenshi_extractor by Toufik BEN JAA',
    }

    if mod_file.header.description:
        po.append(polib.POEntry(
            msgctxt='header::description',
            msgid=mod_file.header.description,
            msgstr='',
        ))

    for item in mod_file.items:
        if not _item_is_translatable(item):
            continue

        for k, v in item.fields.strings.items():
            if not _field_is_translatable(item, k):
                continue

            po_entry = polib.POEntry(
                msgctxt=f'{item.identifier}::{item.item_type.name}::{k}',
                msgid=v,
                msgstr='',
            )
            po.append(po_entry)

    return po