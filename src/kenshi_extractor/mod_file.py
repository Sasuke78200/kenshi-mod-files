from dataclasses import dataclass, field
from pathlib import Path

from binary_reader import BinaryReader
from binary_writer import BinaryWriter
from mod_item import ModItemParser, ModItem, ModItemWriter


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
    """ Dataclass holding parsed .mod files for Kenshi game
        The files are actually called GameDataContainer in the game binary
    """
    path        : Path
    filename    : str
    header      : ModFileHeader
    items       : list[ModItem]

    @classmethod
    def load(cls, path: str | Path) -> "ModFile":
        return ModFileParser(path).parse()

    def save(self, path: str | Path) -> bool:
        return ModFileWriter(self, path).write()

class ModFileWriter:
    def __init__(self, mod_file: ModFile, path: str | Path):
        self.path       = Path(path)
        self.mod_file   = mod_file

    def write(self) -> bool:
        if self.mod_file is None:
            return False

        with self.path.open('wb') as f:
            writer = BinaryWriter(f)
            self._write_header(writer)
            self._write_items(writer)

        return True

    def _write_header(self, writer: BinaryWriter) -> None:
        header = self.mod_file.header
        writer.u32(header.file_version)

        if header.file_version <= 15:
            raise NotImplementedError(f'Unsupported file version: {header.file_version}')

        offset_pos = 0
        if header.file_version >= 17:
            offset_pos = writer.tell()
            writer.u32(0) # placeholder

        writer.u32(header.version)
        writer.string(header.author)
        writer.string(header.description)
        self._write_csv(writer, header.dependencies)
        self._write_csv(writer, header.referenced)

        self._write_optional_unknown_header(writer)
        end_pos = writer.tell()

        if header.file_version >= 17:
            writer.seek(offset_pos, 0)
            writer.u32(end_pos - (offset_pos + 4))
            writer.seek(end_pos, 0)

        writer.s32(header.last_id)
        writer.s32(header.item_count)

    def _write_optional_unknown_header(self, writer: BinaryWriter) -> None:
        header = self.mod_file.header
        if header.save_counter is None:
            return

        writer.u32(header.save_counter)
        writer.u32(header.last_merge_resolve)

        writer.u8(len(header.merge_entries))
        for e in header.merge_entries:
            writer.string(e.filename)
            writer.u32(e.item_1)
            writer.u32(e.item_2)

        writer.u8(len(header.delete_requests))
        for r in header.delete_requests:
            writer.string(r.filename)
            writer.u32(r.version)
            self._write_csv(writer, r.items, ':')

    def _write_items(self, writer: BinaryWriter) -> None:
        item_writer = ModItemWriter(writer, self.mod_file.items, self.mod_file.header.file_version)
        item_writer.write()

    def _write_csv(self, writer: BinaryWriter, values: list, separator: str = ',') -> None:
        writer.string(separator.join(values))


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

    def _read_csv(self, reader: BinaryReader, separator: str = ',') -> list[str]:
        value = reader.string()
        if not value:
            return []
        return [p for p in value.split(separator) if p]

    def _parse_header(self, reader: BinaryReader) -> ModFileHeader:
        header = ModFileHeader(reader.u32())
        if header.file_version < 8 or header.file_version > 17:
            raise NotImplementedError(f'Unsupported file version: {header.file_version}')

        if header.file_version >= 17:
            header.optional_end_offset = reader.u32() + reader.tell()

        if header.file_version > 15:
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
                reader.string(), reader.u32(), self._read_csv(reader, ':')
            ))

    def _parse_items(self, reader: BinaryReader, header: ModFileHeader) -> list[ModItem]:
        parser = ModItemParser(reader, header.file_version, self.filename)
        return [
            parser.parse()
            for _ in range(header.item_count)
        ]