#!/bin/env python3
import argparse

from pathlib import Path
from rich.console import Group
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.tree import Tree
from textual.app import App, ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static

from mod_file import ModFile


class ModBrowserApp(App):
    TITLE = "Kenshi .mod Browser - By Toufik BEN JAA"

    CSS = """
    ListView {
        width: 0.5fr;
        border: solid white;
    }
    VerticalScroll#metadata {
        max-height: 30%;
    }
    VerticalScroll#details {
        width: 2fr;
        border: solid white;
        padding: 1 2;
    }
    """

    BINDINGS = [
        ('q', 'quit', 'Quit'),
    ]

    def __init__(self, mod_file: ModFile):
        super().__init__()
        self.mod_file = mod_file

    def compose(self) -> ComposeResult:
        yield Header()
        with VerticalScroll(id='metadata'):
            yield self._build_metadata()
        with Horizontal():
            yield self._build_items_list()
            with VerticalScroll(id='details'):
                yield Static('Select an item', id='details-content')
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        _, index = event.item.id.split('_')
        self.query_one('#details-content', Static).update(self._build_item_details(int(index)))

    def _build_metadata(self) -> Static:
        metadata = Table.grid(padding=(0, 5))
        metadata.add_column(style='bold green')
        metadata.add_column()
        metadata.add_row('File Version',        str(self.mod_file.header.file_version))
        metadata.add_row('Author',              str(self.mod_file.header.author))
        metadata.add_row('Version',             str(self.mod_file.header.version))
        metadata.add_row('Dependencies',        str(self.mod_file.header.dependencies))
        metadata.add_row('Referenced',          str(self.mod_file.header.referenced))
        metadata.add_row('Save counter',        str(self.mod_file.header.save_counter))
        metadata.add_row('Last Merge Resolve',  str(self.mod_file.header.last_merge_resolve))
        metadata.add_row('Merge Entries count', str(len(self.mod_file.header.merge_entries)))
        metadata.add_row('Delete Request count',str(len(self.mod_file.header.delete_requests)))
        metadata.add_row('Last id',             str(self.mod_file.header.last_id))
        metadata.add_row('Items count',         str(self.mod_file.header.item_count))

        description_panel = Panel(
            escape(str(self.mod_file.header.description)),
            title='[green]Description[/green]',
            title_align='left',
            highlight=True,
        )
        metadata_group = Group(metadata, description_panel)
        metadata_panel = Panel(metadata_group, title="[bold][red]Metadata[/red][/bold]")
        return Static(metadata_panel, id='metadata-content')

    def _build_items_list(self) -> ListView:
        items = []
        for idx, item in enumerate(self.mod_file.items):
            items.append(
                ListItem(
                    Label(item.name),
                    id=f'item_{idx}',
                )
            )
        return ListView(*items)

    def _build_item_details(self, index: int) -> Group:
        item = self.mod_file.items[index]

        save_counter, load_flags = item.unpack_flags()
        load_flags_str = ' | '.join(lf.name for lf in load_flags)

        details = Table.grid(padding=(0, 5))
        details.add_column(style='bold green')
        details.add_column()
        details.add_row('Name',         item.name)
        details.add_row('Type',         item.item_type.name)
        details.add_row('Id',           str(item.item_id))
        details.add_row('Identifier',   item.identifier)
        details.add_row('Flags',        f'0x{item.flags:04x} (Save Counter: 0x{save_counter:04x} Item Load flags: {load_flags_str})')
        details.add_row('Legacy Flags', str(item.legacy_flags))
        details.add_row('Objects',      str(len(item.objects)))

        tables = []
        fields = {
            'Booleans': 'bools',
            'Floats': 'floats',
            'Integers': 'ints',
            'Vector3': 'vectors',
            'Quaternion': 'quaternions',
            'Strings': 'strings',
            'Filenames': 'filenames',
        }

        for name, field in fields.items():
            values = getattr(item.fields, field)
            if len(values) == 0:
                continue

            table = Table(
                title=f'[bold green]{name}[/bold green] - (count: {len(values)})',
                title_style='',
                title_justify='left',
                expand=True,
            )
            table.add_column('Name')
            table.add_column('Value')
            for n, v in values.items():
                table.add_row(n, str(v))
            tables.append(table)

        if item.fields.references:
            # references
            references_tree = Tree(
                f'[bold green]References[/bold green] - (count: {len(item.fields.references)})',
                guide_style='green',
            )
            for section, entries in item.fields.references.items():
                branch = references_tree.add(f'[green]{escape(section)}[/green] (count - {len(entries)})')
                for ref_id, triple in entries.items():
                    branch.add(f'{escape(ref_id)}: {triple}')

            tables.append(references_tree)

        # grouping
        return Group(
            details,            # item details
            Text(''),           # spacing between details and fields
            *tables,            # fields
        )


def cmd_view(path: Path | str) -> None:
    mod_file = ModFile.load(path)
    ModBrowserApp(mod_file).run()


def main():
    parser = argparse.ArgumentParser(description='Tool to manipulate .mod files to Kenshi.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    # view
    view_cmd = subparsers.add_parser('view', help='View .mod content (interactive)')
    view_cmd.add_argument('file', type=Path)
    # extract

    # build

    args = parser.parse_args()

    match args.command:
        case 'view':
            cmd_view(args.file)
        case 'extract':
            pass
        case 'build':
            pass


if __name__ == '__main__':
    main()