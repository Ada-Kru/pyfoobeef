def param_value_to_str(value):
    val_type = type(value)
    if val_type is str:
        return value
    if val_type is bool:
        return "true" if value else "false"
    if val_type is list or val_type is tuple:
        return ",".join(value)
    if val_type is dict or val_type is set:
        return ",".join(value.keys())
    if val_type in (int, float):
        return str(value)
    # uses __name__ to avoid circular import issues
    if val_type.__name__ == "PlaylistInfo":
        return value.id
    if val_type.__name__ == "FileSystemEntry":
        return value.path


def process_column_map(column_map):
    map_type = type(column_map)
    if map_type is None:
        return {}
    elif map_type is dict:
        return column_map
    elif map_type in (set, list, tuple):
        return {key: key for key in column_map}


def seconds_to_hhmmss(total_seconds: float) -> str:
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    hours, minutes, seconds = int(hours), int(minutes), int(seconds)
    return f"{hours:0>2}:{minutes:0>2}:{seconds:0>2}"


def seconds_to_mmss(total_seconds: float) -> str:
    minutes, seconds = divmod(total_seconds, 60)
    minutes, seconds = int(minutes), int(seconds)
    return f"{minutes}:{seconds:0>2}"
