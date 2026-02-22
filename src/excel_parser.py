"""Excel parser for video clip definitions."""
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from openpyxl import load_workbook


@dataclass
class ClipDefinition:
    """Definition of a video clip to extract."""
    start_time: datetime
    end_time: datetime
    description: str
    
    @property
    def duration_seconds(self) -> float:
        """Calculate clip duration in seconds."""
        return (self.end_time - self.start_time).total_seconds()
    
    def get_output_filename(self) -> str:
        """Generate output filename from description."""
        # Clean description for filename
        clean_desc = self.description.strip()
        # Remove invalid filename characters
        for char in '<>:"/\\|?*':
            clean_desc = clean_desc.replace(char, '_')
        return f"{clean_desc}.mp4"


def parse_time_string(time_str: str) -> datetime | None:
    """
    Parse time string in various formats.
    
    Supports:
    - "起 2026-01-15 10:45:02 止 2026-01-15 11:30:00"
    - "2026-01-15 10:45:02"
    """
    import re
    
    # Pattern for datetime
    pattern = r'(\d{4})[-.](\d{2})[-.](\d{2})[\s_](\d{2}):(\d{2}):(\d{2})'
    match = re.search(pattern, time_str)
    
    if match:
        try:
            return datetime(
                int(match.group(1)), int(match.group(2)), int(match.group(3)),
                int(match.group(4)), int(match.group(5)), int(match.group(6))
            )
        except ValueError:
            return None
    
    return None


def parse_excel_clips(excel_path: Path) -> list[ClipDefinition]:
    """
    Parse Excel file to extract clip definitions.
    
    Expected columns:
    - "起始时间点" (Start time)
    - "问题描述" (Description)
    
    The start time column contains strings like:
    "起 yyyy-mm-dd hh:mm:ss 止 yyyy-mm-dd hh:mm:ss"
    
    Args:
        excel_path: Path to Excel file
    
    Returns:
        List of ClipDefinition objects
    """
    clips = []
    
    try:
        workbook = load_workbook(excel_path, data_only=True)
        sheet = workbook.active
        
        # Find column indices
        header_row = 1
        time_col = None
        desc_col = None
        
        for col_idx, cell in enumerate(sheet[header_row], start=1):
            cell_value = str(cell.value or "").strip()
            if "起始时间" in cell_value or "开始时间" in cell_value:
                time_col = col_idx
            elif "问题" in cell_value or "描述" in cell_value or "标题" in cell_value:
                desc_col = col_idx
        
        if not time_col or not desc_col:
            # Try common column names in Chinese
            for col_idx, cell in enumerate(sheet[header_row], start=1):
                cell_value = str(cell.value or "").strip().lower()
                if cell_value in ["起始时间点", "起始时间", "开始时间"]:
                    time_col = col_idx
                elif cell_value in ["问题描述", "描述", "标题", "片段名称"]:
                    desc_col = col_idx
        
        if not time_col or not desc_col:
            return clips
        
        # Parse data rows
        for row_idx in range(header_row + 1, sheet.max_row + 1):
            time_cell = sheet.cell(row=row_idx, column=time_col)
            desc_cell = sheet.cell(row=row_idx, column=desc_col)
            
            time_str = str(time_cell.value or "").strip()
            desc = str(desc_cell.value or "").strip()
            
            if not time_str or not desc:
                continue
            
            # Parse start and end times from the time string
            # Expected format: "起 yyyy-mm-dd hh:mm:ss 止 yyyy-mm-dd hh:mm:ss"
            import re
            
            # Extract all datetime patterns
            pattern = r'(\d{4})[-.](\d{2})[-.](\d{2})[\s_:](\d{2}):(\d{2}):(\d{2})'
            matches = re.findall(pattern, time_str)
            
            if len(matches) >= 2:
                try:
                    start_time = datetime(
                        int(matches[0][0]), int(matches[0][1]), int(matches[0][2]),
                        int(matches[0][3]), int(matches[0][4]), int(matches[0][5])
                    )
                    end_time = datetime(
                        int(matches[1][0]), int(matches[1][1]), int(matches[1][2]),
                        int(matches[1][3]), int(matches[1][4]), int(matches[1][5])
                    )
                    
                    clips.append(ClipDefinition(
                        start_time=start_time,
                        end_time=end_time,
                        description=desc
                    ))
                except ValueError:
                    continue
        
        workbook.close()
        
    except Exception as e:
        print(f"Error parsing Excel: {e}")
    
    return clips
