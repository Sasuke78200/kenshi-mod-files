from dataclasses import dataclass, field
from pathlib import Path

from binary_reader import BinaryReader
from mod_item import ModItemParser, ModItem


@dataclass(slots=True)
class MergeEntry:
    filename    : str
    item_1      : int  # version
    item_2      : int  # version


@dataclass(slots=True)
class DeleteRequests:
    filename    : str
    version     : int
    items       : list[str]


@dataclass(slots=True)
class ModFileHeader:
    file_version        : int
    version             : int | None = None
    author              : str | None = None
    description         : str | None = None
    dependencies        : list[str] = field(default_factory=list)
    referenced          : list[str] = field(default_factory=list)
    optional_end_offset : int = 0
    save_counter        : int | None = None
    last_merge_resolve  : int | None = None
    merge_entries       : list[MergeEntry] = field(default_factory=list)
    delete_requests     : list[DeleteRequests] = field(default_factory=list)
    last_id             : int | None = None
    item_count          : int = 0


@dataclass(slots=True)
class ModFile:
    path        : Path
    filename    : str
    header      : ModFileHeader
    items       : list[ModItem]

    @classmethod
    def load(cls, path: str | Path) -> "ModFile":
        return ModFileParser(path).parse()


class ModFileParser:
    def __init__(self, path: str | Path):
        self.path       = Path(path)
        self.filename   = self.path.name

    def parse(self) -> ModFile:
        if not self.path.exists():
            raise FileNotFoundError(self.path)

        with self.path.open('rb') as f:
            reader = BinaryReader(f)
            header = self._parse_header(reader)
            items = self._parse_items(reader, header)

        return ModFile(self.path, self.filename, header, items)

    def _read_csv(self, reader) -> list[str]:
        value = reader.string()
        if not value:
            return []
        return [p for p in value.split(',') if p]

    def _parse_header(self, reader: BinaryReader) -> ModFileHeader:
        header = ModFileHeader(reader.u32())
        if header.file_version <= 15:
            raise NotImplementedError(f'Unsupported file version: {header.file_version}')

        if header.file_version >= 17:
            header.optional_end_offset = reader.u32()

        header.version      = reader.u32()
        header.author       = reader.string()
        header.description  = reader.string()
        header.dependencies = self._read_csv(reader)
        header.referenced   = self._read_csv(reader)

        self._read_optional_unknown_header(reader, header)

        if header.optional_end_offset > 0:
            reader.seek(header.optional_end_offset, 0)

        header.last_id      = reader.s32()
        header.item_count   = reader.s32()
        return header

    def _read_optional_unknown_header(self, reader: BinaryReader, header: ModFileHeader) -> None:
        if reader.tell() >= header.optional_end_offset:
            return

        header.save_counter         = reader.u32()
        header.last_merge_resolve   = reader.u32()

        for _ in range(reader.u8()):
            header.merge_entries.append(MergeEntry(
                reader.string(), reader.u32(), reader.u32()
            ))

        if reader.tell() >= header.optional_end_offset:
            return

        for _ in range(reader.u8()):
            header.delete_requests.append(DeleteRequests(
                reader.string(), reader.u32(), self._read_csv(reader)
            ))

    def _parse_items(self, reader: BinaryReader, header: ModFileHeader) -> list[ModItem]:
        parser = ModItemParser(reader, header.file_version, self.filename)
        return [
            parser.parse()
            for _ in range(header.item_count)
        ]