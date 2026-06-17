import os
import zipfile
import xml.etree.ElementTree as ET

class JDParser:
    def __init__(self, file_path=None, jd_text=None):
        self.file_path = file_path
        if jd_text is not None:
            self.raw_text = jd_text
        else:
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
        """
        Dynamically extracts disqualifier patterns from the JD text.
        Falls back to sensible defaults if extraction fails.
        """
        text = self.raw_text.lower()
        
        # Start with defaults
        disqualifiers = {
            'consulting_only': ['tcs', 'wipro', 'infosys', 'accenture', 'cognizant', 'capgemini'],
            'non_tech': ['marketing', 'hr', 'sales', 'graphic', 'support', 'writer', 'accountant'],
            'academic_only': ['research lab', 'postdoc', 'academic researcher', 'publication only'],
            'adjacent_fields': []
        }
        
        # Dynamically detect consulting companies mentioned in JD
        consulting_keywords = [
            'tcs', 'wipro', 'infosys', 'accenture', 'cognizant', 'capgemini',
            'hcl', 'tech mahindra', 'deloitte', 'kpmg', 'ey', 'pwc'
        ]
        found_consulting = [c for c in consulting_keywords if c in text]
        if found_consulting:
            disqualifiers['consulting_only'] = found_consulting
        
        # Dynamically detect "do NOT want" patterns from JD
        adjacent = []
        adjacent_keywords = [
            'speech recognition', 'computer vision', 'robotics', 
            'audio processing', 'image processing', 'autonomous driving',
            'hardware', 'embedded systems'
        ]
        # Only flag adjacent fields if JD explicitly mentions them as NOT wanted
        not_want_section = False
        for line in self.raw_text.split('\n'):
            line_lower = line.lower().strip()
            if 'do not want' in line_lower or 'not looking for' in line_lower or 'disqualif' in line_lower:
                not_want_section = True
            elif not_want_section and line_lower == '':
                not_want_section = False
            
            if not_want_section:
                for kw in adjacent_keywords:
                    if kw in line_lower and kw not in adjacent:
                        adjacent.append(kw)
        
        # Also check for explicit mentions of "pure research" or "academic only" disqualifiers
        if 'pure research' in text or 'research-only' in text or 'academic labs' in text:
            if 'research lab' not in disqualifiers['academic_only']:
                disqualifiers['academic_only'].append('research lab')
        
        if adjacent:
            disqualifiers['adjacent_fields'] = adjacent
            
        return disqualifiers

