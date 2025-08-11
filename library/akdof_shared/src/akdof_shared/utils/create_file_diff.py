import difflib
from pathlib import Path

def create_file_diff(file_a: Path, file_b: Path, output_directory: Path) -> None | Path:
    """Create a GitHub-style diff between any two files that can be read using file.readlines() and save as HTML."""

    output_directory.mkdir(parents=True, exist_ok=True)
    
    with open(file_a, "r") as f:
        lines_a = f.readlines()
    with open(file_b, "r") as f:
        lines_b = f.readlines()

    if lines_a == lines_b:
        return None
    
    differ = difflib.HtmlDiff(wrapcolumn=80)
    diff_html = differ.make_file(
        lines_a, 
        lines_b,
        fromdesc=f"a/{file_a.name}",
        todesc=f"b/{file_b.name}",
        context=True,
    )
    
    output_filename = f"{file_a.stem}_diff_{file_b.stem}.html"
    output_path = output_directory / output_filename
    
    with open(output_path, "w") as f:
        f.write(diff_html)

    return output_path