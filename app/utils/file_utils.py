

def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}".replace(".", ",") + " KB"
    return f"{size_bytes / (1024 * 1024):.1f}".replace(".", ",") + " MB"