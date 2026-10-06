import io
import pandas as pd
from typing import List, Dict, Any

def export_to_excel(data: List[Dict[str, Any]], sheet_name: str = "Report") -> bytes:
    df = pd.DataFrame(data)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    buffer.seek(0)
    return buffer.getvalue()

def export_to_csv(data: List[Dict[str, Any]]) -> bytes:
    df = pd.DataFrame(data)
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False, encoding='utf-8')
    buffer.seek(0)
    return buffer.getvalue()
