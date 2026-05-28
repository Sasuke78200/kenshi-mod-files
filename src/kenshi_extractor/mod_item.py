from dataclasses import dataclass
from enum import IntEnum

from binary_reader import BinaryReader



class ItemType(IntEnum):
    BUILDING = 0
    CHARACTER = 1
    WEAPON = 2
    ARMOUR = 3
    ITEM = 4
    ANIMAL_ANIMATION = 5
    ATTACHMENT = 6
    RACE = 7
    LOCATION = 8
    WAR_SAVESTATE = 9
    FACTION = 10
    NULL_ITEM = 11
    ZONE_MAP = 12
    TOWN = 13
    WORLDMAP_CHARACTER = 14
    CHARACTER_APPEARANCE_OLD = 15
    LOCATIONAL_DAMAGE = 16
    COMBAT_TECHNIQUE = 17
    DIALOGUE = 18
    DIALOGUE_LINE = 19
    TECHTREE = 20
    RESEARCH = 21
    AI_TASK = 22
    AI_STATE = 23
    ANIMATION = 24
    STATS = 25
    PERSONALITY = 26
    CONSTANTS = 27
    BIOMES = 28
    BUILDING_PART = 29
    INSTANCE_COLLECTION = 30
    DIALOG_ACTION = 31
    TEMPORARY_INFO = 32
    MOD_FILENAME = 33
    PLATOON = 34
    GAMESTATE_BUILDING = 35
    GAMESTATE_CHARACTER = 36
    GAMESTATE_FACTION = 37
    GAMESTATE_TOWN_INSTANCE_LIST = 38
    STATE = 39
    SAVED_STATE = 40
    INVENTORY_STATE = 41
    INVENTORY_ITEM_STATE = 42
    REPEATABLE_BUILDING_PART_SLOT = 43
    MATERIAL_SPEC = 44
    MATERIAL_SPECS_COLLECTION = 45
    CONTAINER = 46
    MATERIAL_SPECS_CLOTHING = 47
    GAMESTATE_BUILDING_INTERIOR = 48
    VENDOR_LIST = 49
    MATERIAL_SPECS_WEAPON = 50
    WEAPON_MANUFACTURER = 51
    SQUAD_TEMPLATE = 52
    ROAD = 53
    LOCATION_NODE = 54
    COLOR_DATA = 55
    CAMERA = 56
    MEDICAL_STATE = 57
    MEDICAL_PART_STATE = 58
    FOLIAGE_LAYER = 59
    FOLIAGE_MESH = 60
    GRASS = 61
    BUILDING_FUNCTIONALITY = 62
    DAY_SCHEDULE = 63
    NEW_GAME_STARTOFF = 64
    GAMESTATE_CRAFTING = 65
    CHARACTER_APPEARANCE = 66
    GAMESTATE_AI = 67
    WILDLIFE_BIRDS = 68
    MAP_FEATURES = 69
    DIPLOMATIC_ASSAULTS = 70
    SINGLE_DIPLOMATIC_ASSAULT = 71
    AI_PACKAGE = 72
    DIALOGUE_PACKAGE = 73
    GUN_DATA = 74
    HUMAN_CHARACTER = 75
    ANIMAL_CHARACTER = 76
    UNIQUE_SQUAD_TEMPLATE = 77
    FACTION_TEMPLATE = 78
    AI_SCHEDULE = 79
    WEATHER = 80
    SEASON = 81
    EFFECT = 82
    ITEM_PLACEMENT_GROUP = 83
    WORD_SWAPS = 84
    NEST = 85
    NEST_ITEM = 86
    CHARACTER_PHYSICS_ATTACHMENT = 87
    LIGHT = 88
    HEAD = 89
    BLUEPRINT = 90
    SHOP_TRADER_CLASS = 91
    FOLIAGE_BUILDING = 92
    FACTION_CAMPAIGN = 93
    GAMESTATE_TOWN = 94
    BIOME_GROUP = 95
    EFFECT_FOG_VOLUME = 96
    FARM_DATA = 97
    FARM_PART = 98
    ENVIRONMENT_RESOURCES = 99
    RACE_GROUP = 100
    ARTIFACTS = 101
    MAP_ITEM = 102
    BUILDINGS_SWAP = 103
    ITEMS_CULTURE = 104
    ANIMATION_EVENT = 105
    TUTORIAL = 106
    CROSSBOW = 107
    TERRAIN_DECALS = 108
    AMBIENT_SOUND = 109
    WORLD_EVENT_STATE = 110
    LIMB_REPLACEMENT = 111
    ANIMATION_FILE = 112
    ____XXX___ = 113
    OBJECT_TYPE_MAX = 114


@dataclass(frozen=True, slots=True)
class Vector3:
    x : float
    y : float
    z : float

@dataclass(frozen=True, slots=True)
class Quaternion:
    x : float
    y : float
    z : float
    w : float

@dataclass(frozen=True, slots=True)
class TripleInt:
    v0 : int
    v1 : int = 0
    v2 : int = 0


@dataclass(slots=True)
class ModItemFields:
    bools       : dict[str, bool]
    floats      : dict[str, float]
    ints        : dict[str, int]
    vectors     : dict[str, Vector3]
    quaternions : dict[str, Quaternion]
    strings     : dict[str, str]
    filenames   : dict[str, str]
    triples     : dict[str, dict[str, TripleInt]]

@dataclass(slots=True)
class ModObject:
    identifier          : str
    reference           : str
    position            : Vector3
    rotation            : Quaternion
    extra_references    : list


@dataclass(slots=True)
class ModItem:
    unknown_0000    : int
    item_type       : ItemType
    item_id         : int
    name            : str
    identifier      : str
    flags           : int
    legacy_flags    : dict
    fields          : ModItemFields
    objects         : list[ModObject]

class ModItemParser:
    def __init__(self, reader: BinaryReader, file_version: int, filename: str) -> None:
        self.reader = reader
        self.file_version = file_version
        self.filename = filename

    def parse(self) -> ModItem:
        unknown_0000    = self.reader.s32()
        item_type       = ItemType(self.reader.s32())
        item_id         = self.reader.s32()
        name            = self.reader.string()
        identifier      = self._read_identifier(item_id)

        flags, legacy_flags = self._read_flags()
        fields          = self._read_fields()
        objects         = self._read_objects()

        return ModItem(
            unknown_0000, item_type, item_id,
            name, identifier, flags, legacy_flags,
            fields, objects
        )

    def _read_identifier(self, item_id: int) -> str:
        if self.file_version >= 7:
            return self.reader.string()
        return f'{item_id}-{self.filename}'

    def _read_flags(self) -> tuple[int, dict[str, bool]]:
        if self.file_version >= 15:
            return self.reader.u32(), {}

        legacy_flags = {}
        if self.file_version >= 11:
            count = self.reader.s32()
            if count > 0 and self.filename != 'gamedata.base':
                for _ in range(count):
                    flag_name = self.reader.string()
                    legacy_flags[flag_name] = self.reader.boolean()

        return 0, legacy_flags

    def _read_vector3(self) -> Vector3:
        return Vector3(self.reader.f32(), self.reader.f32(), self.reader.f32())

    def _read_fields(self) -> ModItemFields:
        bools   = self._read_keyed_fields(self.reader.boolean)
        floats  = self._read_keyed_fields(self.reader.f32)
        ints    = self._read_keyed_fields(self.reader.s32)

        vectors, quaternions = {}, {}
        if self.file_version > 8:
            vectors = self._read_keyed_fields(self._read_vector3)
            quaternions = self._read_keyed_fields(lambda: Quaternion(self.reader.f32(), self.reader.f32(), self.reader.f32(), self.reader.f32()))

        strings     = self._read_keyed_fields(self.reader.string)
        filenames   = self._read_keyed_fields(self.reader.string)
        triples     = self._read_triples()

        return ModItemFields(
            bools, floats, ints,
            vectors, quaternions,
            strings, filenames,
            triples
        )

    def _read_keyed_fields(self, reader: callable) -> dict:
        fields = {}
        for _ in range(self.reader.s32()):
            key = self.reader.string()
            fields[key] = reader()
        return fields

    def _read_triples(self) -> dict[str, dict[str, TripleInt]]:
        triple_ints = {}
        for _ in range(self.reader.s32()):
            key = self.reader.string()
            triple_ints[key] = {}

            for _ in range(self.reader.s32()):
                if self.file_version < 8:
                    self.reader.s64() # unused
                    continue
                ref_id = self.reader.string()
                triple_int = None
                if self.file_version >= 10:
                    triple_int = TripleInt(self.reader.s32(), self.reader.s32(), self.reader.s32())
                else:
                    triple_int = TripleInt(self.reader.s32())

                triple_ints[key][ref_id] = triple_int

        return triple_ints

    def _read_object_identifier(self) -> str:
        if self.file_version >= 15:
            return self.reader.string()
        return f'{self.reader.s32()}-{self.filename}'

    def _read_objects(self) -> list[ModObject]:
        objects = []

        for _ in range(self.reader.s32()):
            identifier = self._read_object_identifier()
            reference = "" if self.file_version < 8 else self.reader.string()

            position = self._read_vector3()

            qw = self.reader.f32()
            qx = self.reader.f32()
            qy = self.reader.f32()
            qz = self.reader.f32()

            extra_references = []

            if self.file_version > 6:
                for _ in range(self.reader.s32()):
                    extra_references.append(self._read_object_extra_reference())

            objects.append(ModObject(
                identifier=identifier,
                reference=reference,
                position=position,
                rotation=Quaternion(qx, qy, qz, qw),
                extra_references=extra_references,
            ))

        return objects

    def _read_object_extra_reference(self) -> str:
        if self.file_version >= 15:
            return self.reader.string()
        return f'{self.reader.s32()}-{self.filename}-INGAME'
