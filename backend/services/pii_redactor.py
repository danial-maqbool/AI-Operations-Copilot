import re
from typing import Tuple, Dict

EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
PHONE_REGEX = re.compile(r'\(?\b[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b')
SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')
CC_REGEX = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')

class PIIRedactor:
    @classmethod
    def redact(cls, text: str) -> Tuple[str, Dict[str, str]]:
        mapping = {}
        counter = {"email": 1, "phone": 1, "ssn": 1, "cc": 1}

        def replace_email(match):
            placeholder = f"[EMAIL_{counter['email']}]"
            counter["email"] += 1
            mapping[placeholder] = match.group(0)
            return placeholder

        def replace_phone(match):
            placeholder = f"[PHONE_{counter['phone']}]"
            counter["phone"] += 1
            mapping[placeholder] = match.group(0)
            return placeholder

        def replace_ssn(match):
            placeholder = f"[SSN_{counter['ssn']}]"
            counter["ssn"] += 1
            mapping[placeholder] = match.group(0)
            return placeholder

        def replace_cc(match):
            placeholder = f"[CC_{counter['cc']}]"
            counter["cc"] += 1
            mapping[placeholder] = match.group(0)
            return placeholder

        redacted = EMAIL_REGEX.sub(replace_email, text)
        redacted = PHONE_REGEX.sub(replace_phone, redacted)
        redacted = SSN_REGEX.sub(replace_ssn, redacted)
        redacted = CC_REGEX.sub(replace_cc, redacted)

        return redacted, mapping

    @classmethod
    def restore(cls, text: str, mapping: Dict[str, str]) -> str:
        restored = text
        for placeholder, original in mapping.items():
            restored = restored.replace(placeholder, original)
        return restored
