from typing import Dict, List, Optional, Any
from pathlib import Path
import re

from ..config import Config
from ..models.schemas import ReportData, HealthIndicator


class ReportParser:
    def __init__(self, config: Config):
        self.config = config
        self.report_config = config.report

    async def parse_report(self, file_path: str) -> ReportData:
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if path.suffix.lower() != ".pdf":
            raise ValueError(f"不支持的文件格式: {path.suffix}")

        text = await self._extract_text(file_path)

        basic_info = self._parse_basic_info(text)
        indicators = self._parse_indicators(text)
        abnormal_list = self._parse_abnormal_indicators(indicators)
        doctor_advice = self._parse_doctor_advice(text)

        return ReportData(
            report_date=self._extract_report_date(text),
            basic_info=basic_info,
            indicators=indicators,
            abnormal_list=abnormal_list,
            doctor_advice=doctor_advice
        )

    async def _extract_text(self, file_path: str) -> str:
        try:
            import pymupdf
            doc = pymupdf.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            raise Exception(f"提取PDF文本失败: {e}")

    def _parse_basic_info(self, text: str) -> Dict[str, Any]:
        basic_info = {}

        height_match = re.search(r'身高[：:]\s*(\d+(?:\.\d+)?)\s*(?:cm|厘米)?', text)
        if height_match:
            basic_info["height"] = float(height_match.group(1))

        weight_match = re.search(r'体重[：:]\s*(\d+(?:\.\d+)?)\s*(?:kg|公斤)?', text)
        if weight_match:
            basic_info["weight"] = float(weight_match.group(1))

        if "height" in basic_info and "weight" in basic_info:
            height_m = basic_info["height"] / 100
            basic_info["bmi"] = round(basic_info["weight"] / (height_m ** 2), 1)

        bp_match = re.search(r'血压[：:]\s*(\d+)/(\\d+)\s*(?:mmHg)?', text)
        if bp_match:
            basic_info["blood_pressure"] = {
                "systolic": int(bp_match.group(1)),
                "diastolic": int(bp_match.group(2))
            }

        hr_match = re.search(r'心率[：:]\s*(\d+)\s*(?:次/分|bpm)?', text)
        if hr_match:
            basic_info["heart_rate"] = int(hr_match.group(1))

        return basic_info

    def _parse_indicators(self, text: str) -> List[Dict[str, Any]]:
        indicators = []

        indicator_patterns = [
            r'(\w+)\s*[：:]\s*(\d+(?:\.\d+)?)\s*([^\s]+)\s*(?:参考值|正常值)[：:]\s*([^\s]+)',
            r'(\w+)\s*[：:]\s*(\d+(?:\.\d+)?)\s*([^\s]+)\s*\[([^\]]+)\]',
        ]

        for pattern in indicator_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                name = match.group(1)
                value = float(match.group(2))
                unit = match.group(3)
                normal_range = match.group(4)

                status = self._determine_status(value, normal_range)

                indicator = {
                    "name": name,
                    "value": value,
                    "unit": unit,
                    "normal_range": normal_range,
                    "status": status
                }
                indicators.append(indicator)

        return indicators

    def _determine_status(self, value: float, normal_range: str) -> str:
        range_match = re.search(r'(\d+(?:\.\d+)?)\s*[-~至]\s*(\d+(?:\.\d+)?)', normal_range)
        if range_match:
            min_val = float(range_match.group(1))
            max_val = float(range_match.group(2))
            if value < min_val:
                return "low"
            elif value > max_val:
                return "high"
            else:
                return "normal"

        return "unknown"

    def _parse_abnormal_indicators(self, indicators: List[Dict[str, Any]]) -> List[str]:
        abnormal_list = []
        for indicator in indicators:
            if indicator.get("status") in ["high", "low"]:
                abnormal_list.append(indicator["name"])
        return abnormal_list

    def _parse_doctor_advice(self, text: str) -> str:
        advice_patterns = [
            r'医生建议[：:]\s*([^\n]+)',
            r'建议[：:]\s*([^\n]+)',
            r'注意事项[：:]\s*([^\n]+)',
        ]

        for pattern in advice_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()

        return "暂无医生建议"

    def _extract_report_date(self, text: str) -> str:
        date_patterns = [
            r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?',
            r'(\d{4})-(\d{2})-(\d{2})',
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                year = match.group(1)
                month = match.group(2).zfill(2)
                day = match.group(3).zfill(2)
                return f"{year}-{month}-{day}"

        return "未知日期"
