import re
from typing import List, Dict, Optional
from src.nlp_engine import Token


class GeometryExtractor:
    KEYWORDS = {
        "CMD_DEFINE": ["дано", "є", "нехай", "мати", "трикутник"],
        "CMD_CONSTRUCT": ["побудувати", "накреслити", "провести", "опустити", "відкласти", "позначити", "позначили"],
        "CMD_CALCULATE": ["знайти", "обчислити", "визначити", "довести"],

        "ENTITY_TRIANGLE": ["трикутник"],
        "ENTITY_ALTITUDE": ["висота"],
        "ENTITY_MEDIAN": ["медіана"],
        "ENTITY_BISECTOR": ["бісектриса"],
        "ENTITY_POINT": ["точка", "точки", "точку"],
        "ENTITY_SEGMENT": ["відрізок", "сторона", "стороні"],
        "ENTITY_ANGLE": ["кут", "кути"],

        "SPEC_ISOSCELES": ["рівнобедрений"],
        "SPEC_RIGHT": ["прямокутний"],
        "SPEC_EQUILATERAL": ["рівносторонній", "правильний"],
    }

    def extract_structure(self, tokens: List[Token]) -> list[dict]:
        if not tokens: return []

        global_specs = []
        for t in tokens:
            s_type = self._get_spec_type(t.lemma)
            if s_type:
                global_specs.append(s_type)

        if global_specs:
            print(f"     [DEBUG EXTRACTOR] Global Specs found: {global_specs}")

        found_entities = []
        for t in tokens:
            e_type = self._get_entity_type(t.lemma)
            if e_type:
                found_entities.append((t, e_type))

        if not found_entities: return []

        extracted_commands = []

        for token, e_type in found_entities:
            if e_type == "segment" and token.lemma in ["сторона", "стороні"]:
                root = next((t for t in tokens if t.head == 0), None)
                if not (root and self._check_keyword(root.lemma, "CMD_CALCULATE")):
                    continue

            labels = self._find_all_labels(token, tokens)

            if not labels:
                labels = [None]

            for label in labels:
                if e_type != "triangle" and label and len(label) == 3:
                    alt_label = self._find_short_label(token, tokens)
                    if alt_label: label = alt_label

                command = "CONSTRUCT"
                if e_type == "triangle": command = "DEFINE"

                root = next((t for t in tokens if t.head == 0), None)
                if root and self._check_keyword(root.lemma, "CMD_CALCULATE") and token.head == root.id:
                    command = "CALCULATE"

                cmd_obj = {
                    "command": command,
                    "entity": e_type,
                    "label": label,
                    "params": {}
                }

                if e_type == "triangle" and global_specs:
                    cmd_obj["params"]["specifications"] = list(set(global_specs))
                elif e_type != "triangle":
                    specs = self._find_specs(token, tokens)
                    if specs: cmd_obj["params"]["specifications"] = specs

                if e_type == "point":
                    target_segment = self._find_connected_segment(token, tokens)
                    if target_segment:
                        cmd_obj["params"]["on_segment"] = target_segment

                val = self._find_value(token, tokens)
                if val: cmd_obj["params"]["value"] = val

                extracted_commands.append(cmd_obj)

        return extracted_commands

    def _find_all_labels(self, parent_token: Token, all_tokens: List[Token]) -> List[str]:
        found_labels = []

        if self._is_valid_label(parent_token.text):
            found_labels.append(parent_token.text)

        for t in all_tokens:
            if t.head == parent_token.id:
                if self._is_valid_label(t.text):
                    if t.deprel in ['parataxis', 'conj', 'appos', 'flat:title', 'flat:foreign', 'nsubj']:
                        found_labels.append(t.text)

                    elif t.deprel == 'nmod':
                        if len(t.text) == 3 and parent_token.lemma != "трикутник":
                            continue
                        found_labels.append(t.text)

        if not found_labels and parent_token.head != 0:
            for t in all_tokens:
                if t.head == parent_token.head and t.id != parent_token.id:
                    if self._is_valid_label(t.text) and t.deprel not in ['nmod', 'conj']:
                        found_labels.append(t.text)

        nsubj = next((t for t in all_tokens if t.head == parent_token.id and t.deprel == 'nsubj'), None)
        if nsubj and self._is_valid_label(nsubj.text):
            found_labels.append(nsubj.text)

        return list(set(found_labels))

    def _is_valid_label(self, text: str) -> bool:
        return bool(re.match(r'^([A-Z]|[А-ЯІЇЄ]){1,3}$', text))

    def _find_conjunctions(self, main_label: str, tokens: List[Token]) -> List[str]:
        return []

    def _get_spec_type(self, lemma: str) -> Optional[str]:
        l = lemma.lower()
        if "рівнобедр" in l: return "isosceles"
        if "рівносторон" in l: return "equilateral"
        if "прямокут" in l: return "right"
        if "правильн" in l: return "equilateral"

        for key, values in self.KEYWORDS.items():
            if key.startswith("SPEC_") and l in values:
                return key.replace("SPEC_", "").lower()
        return None

    def _find_specs(self, parent_token: Token, all_tokens: List[Token]) -> List[str]:
        specs = []
        for t in all_tokens:
            if t.head == parent_token.id:
                s_type = self._get_spec_type(t.lemma)
                if s_type: specs.append(s_type)
        return specs

    def _find_label_for_token(self, token, tokens):
        res = self._find_all_labels(token, tokens)
        return res[0] if res else None

    def _scan_children_for_label(self, token: Token, all_tokens: List[Token]) -> Optional[str]:
        labels = self._find_all_labels(token, all_tokens)
        return labels[0] if labels else None

    def _find_value(self, parent_token: Token, all_tokens: List[Token]) -> Optional[float]:
        for t in all_tokens:
            if t.upos == 'NUM':
                if abs(t.id - parent_token.id) < 6:
                    try:
                        return float(t.text.replace(',', '.'))
                    except:
                        pass
        return None

    def _find_short_label(self, start_token: Token, all_tokens: List[Token]) -> Optional[str]:
        for t in all_tokens:
            if self._is_valid_label(t.text) and len(t.text) == 2:
                return t.text
        return None

    def _find_connected_segment(self, point_token: Token, tokens: List[Token]) -> Optional[str]:
        valid_line_types = ["segment", "median", "altitude", "bisector"]
        for t in tokens:
            e_type = self._get_entity_type(t.lemma)
            if e_type in valid_line_types:
                lbls = self._find_all_labels(t, tokens)
                if lbls: return lbls[0]
        return None

    def _check_keyword(self, lemma: str, key_group: str) -> bool:
        return lemma.lower() in self.KEYWORDS.get(key_group, [])

    def _get_entity_type(self, lemma: str) -> Optional[str]:
        for key, values in self.KEYWORDS.items():
            if key.startswith("ENTITY_") and lemma.lower() in values:
                return key.replace("ENTITY_", "").lower()
        return None