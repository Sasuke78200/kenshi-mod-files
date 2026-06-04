# Kenshi Game Data Container — Binary Format

Files with extensions `.mod`, `.save`, `.zone`, and `.level` all share the same binary container
format, referred to internally as `GameDataContainer`.

Byte order is **little-endian** throughout.

---

## Primitive Types

| Type     | Size     | Description |
|----------|----------|-------------|
| `u8`     | 1 byte   | Unsigned 8-bit integer |
| `s32`    | 4 bytes  | Signed 32-bit integer |
| `u32`    | 4 bytes  | Unsigned 32-bit integer |
| `f32`    | 4 bytes  | IEEE 754 single-precision float |
| `bool`   | 1 byte   | `0x00` = false, any other value = true |
| `string` | variable | `u32` length prefix, followed by that many UTF-8 bytes — no null terminator |
| `vec3`   | 12 bytes | Three consecutive `f32`: `x`, `y`, `z` |
| `quat`   | 16 bytes | Four consecutive `f32`: `x`, `y`, `z`, `w` |
| `ogre_quat`   | 16 bytes | Four consecutive `f32` stored in Ogre::Quaternion layout: `w`, `x`, `y`, `z` |

---

## File Layout

```
[Header]
[Item] × item_count
```

---

## Header

```
u32  file_version

if file_version >= 17:
    u32  section_size       // byte distance from end of this field to first byte of last_id

if file_version > 15:
    u32     version
    string  author
    string  description
    string  dependencies    // comma-separated mod filenames
    string  referenced      // comma-separated mod filenames

    // optional section — only present in file_version >= 17, when section_size > 0
    if cursor < section_end:
        u32  save_counter
        u32  last_merge_resolve

        u8   merge_entry_count
        for _ in range(merge_entry_count):
            string  filename
            u32     version_1
            u32     version_2

        if cursor < section_end:
            u8   delete_request_count
            for _ in range(delete_request_count):
                string  filename
                u32     version
                string  items       // colon-separated item identifiers

    seek to section_end     // skip any unrecognised future fields

s32  last_id
s32  item_count
```

> `section_end` is the absolute file offset: `section_size` + position after reading `section_size`.

> For `file_version <= 15` (e.g. `.save` files), the header contains only `file_version`,
> `last_id`, and `item_count`. No metadata fields are present.

---

## Item

Repeated `item_count` times.

```
s32     unknown             // present for file_version >= 3
                            // always written as 0 by the game; value is discarded on load
s32     item_type           // see CONSTANTS.md — ItemType
s32     item_id
string  name

// identifier
if file_version >= 7:
    string  identifier
else:
    identifier = f'{item_id}-{filename}'

// flags
if file_version >= 15:
    u32  flags              // see CONSTANTS.md — Item Flags
elif file_version in (11, 13, 14):
    s32  legacy_flag_count
    if legacy_flag_count > 0 and filename != 'gamedata.base':
        for _ in range(legacy_flag_count):
            string  flag_name
            bool    flag_value

// typed fields — all sections present unconditionally, each prefixed by their count
s32  bool_count
for _ in range(bool_count):
    string  key
    bool    value

s32  float_count
for _ in range(float_count):
    string  key
    f32     value

s32  int_count
for _ in range(int_count):
    string  key
    s32     value

if file_version > 8:
    s32  vec3_count
    for _ in range(vec3_count):
        string  key
        vec3    value

    s32  quaternion_count
    for _ in range(quaternion_count):
        string  key
        quat    value       // stored as x, y, z, w — NOT the Ogre w-first layout

s32  string_count
for _ in range(string_count):
    string  key
    string  value

s32  filename_count
for _ in range(filename_count):
    string  key
    string  value

// references
s32  ref_section_count
for _ in range(ref_section_count):
    string  section_key
    s32     ref_count
    for _ in range(ref_count):
        if file_version < 8:
            u64  unused             // read and discarded
        else:
            string  ref_id
            s32     v0
            if file_version >= 10:
                s32  v1
                s32  v2
                // v0 == v1 == v2 == 0x7FFFFFFF signals deletion — see CONSTANTS.md

// objects
s32  object_count
for _ in range(object_count):
    [Object — see below]
```

---

## Object

Sub-records inside each item, representing placed instances in the world.

```
// identifier
if file_version >= 15:
    string  identifier
    // NOTE: in .save files this may be a compact binary form:
    //   length = 4, content = s32 little-endian integer
    //   occurs when the stored integer ID >= 128 (invalid as a UTF-8 lead byte)
    //   reconstruct as f'{integer}-{filename}'
else:
    s32     identifier_int
    identifier = f'{identifier_int}-{filename}'

// reference
if file_version >= 8:
    string  reference
else:
    reference = ''

vec3       position
ogre_quat  rotation      // Ogre::Quaternion layout — w is first on disk

// extra references
if file_version > 6:
    s32  extra_ref_count
    for _ in range(extra_ref_count):
        if file_version >= 15:
            string  ref
            // same compact binary edge case as identifier above
        else:
            s32     ref_int
            ref = f'{ref_int}-{filename}-INGAME'
```
