from pathlib import Path
import zipfile
from typing import Iterable


def zip_directory(src_dir: Path, zip_path: Path, include_parent: bool = False) -> None:
	mode = "w"
	with zipfile.ZipFile(str(zip_path), mode, zipfile.ZIP_DEFLATED) as zf:
		src_dir = src_dir.resolve()
		base = src_dir.parent if include_parent else src_dir
		for path in src_dir.rglob("*"):
			if path.is_file():
				arcname = path.relative_to(base)
				zf.write(str(path), str(arcname))
