import os
import zipfile
import xml.etree.ElementTree as ET

class JDParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.raw_text = self._load_jd()
        
    def _load_jd(self):
        """Loads docx or txt job description."""
        if not os.path.exists(self.file_path):
            return ""
            
        if self.file_path.endswith('.docx'):
            try:
                with zipfile.ZipFile(self.file_path) as z:
                    xml_content = z.read('word/document.xml')
                    root = ET.fromstring(xml_content)
                    paragraphs = []
                    for para in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
                        texts = [node.text for node in para.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text]
                        if texts:
                            paragraphs.append("".join(texts))
                    return "\n".join(paragraphs)
            except Exception:
                return ""
        else:
            try:
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception:
                return ""

    def get_disqualifiers(self):
        """Returns hardcoded regex/patterns matching JD exclusions."""
        return {
            'consulting_only': ['tcs', 'wipro', 'infosys', 'accenture', 'cognizant', 'capgemini'],
            'non_tech': ['marketing', 'hr', 'sales', 'graphic', 'support', 'writer', 'accountant'],
            'academic_only': ['research lab', 'postdoc', 'academic researcher', 'publication only'],
            'adjacent_fields': ['speech recognition', 'computer vision', 'robotics', 'audio processing']
        }
