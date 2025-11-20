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

            main_label = self._find_label_for_token(token, tokens)

            if e_type != "triangle" and main_label and len(main_label) == 3:
                alt_label = self._find_short_label(token, tokens)
                if alt_label: main_label = alt_label

            labels_to_process = []
            if main_label:
                labels_to_process.append(main_label)
                conjunctions = self._find_conjunctions(main_label, tokens)
                labels_to_process.extend(conjunctions)
            else:
                labels_to_process.append(None)

            for label in labels_to_process:
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
                    for t in tokens:
                        if self._get_entity_type(t.lemma) == "segment":
                            seg_label = self._find_label_for_token(t, tokens)
                            if seg_label:
                                cmd_obj["params"]["on_segment"] = seg_label
                                break

                val = self._find_value(token, tokens)
                if val: cmd_obj["params"]["value"] = val

                extracted_commands.append(cmd_obj)

        return extracted_commands

    def _find_conjunctions(self, main_label: str, tokens: List[Token]) -> List[str]:
        label_token = next((t for t in tokens if t.text == main_label), None)

        if not label_token: return []

        conjs = []
        for t in tokens:
            if t.head == label_token.id and t.deprel == 'conj':
                if re.match(r'^[A-Z]{1,3}$', t.text):
                    conjs.append(t.text)
        return conjs

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

    def _find_label_for_token(self, parent_token: Token, all_tokens: List[Token]) -> Optional[str]:
        if re.match(r'^[A-Z]{1,3}$', parent_token.text): return parent_token.text

        nsubj = next((t for t in all_tokens if t.head == parent_token.id and t.deprel == 'nsubj'), None)
        if nsubj:
            if re.match(r'^[A-Z]{1,3}$', nsubj.text): return nsubj.text
            child_l = self._scan_children_for_label(nsubj, all_tokens)
            if child_l: return child_l

        child_label = self._scan_children_for_label(parent_token, all_tokens)
        if child_label: return child_label

        if parent_token.head != 0:
            for t in all_tokens:
                if t.head == parent_token.head and t.id != parent_token.id:
                    if re.match(r'^[A-Z]{1,3}$', t.text):
                        if t.deprel not in ['nmod', 'conj']:
                            return t.text

        if parent_token.head != 0:
            head = next((t for t in all_tokens if t.id == parent_token.head), None)
            if head and parent_token.deprel in ['appos', 'nmod', 'conj', 'obl']:
                hl = self._scan_children_for_label(head, all_tokens)
                if hl: return hl
                if re.match(r'^[A-Z]{1,3}$', head.text): return head.text
        return None

    def _scan_children_for_label(self, token: Token, all_tokens: List[Token]) -> Optional[str]:
        for t in all_tokens:
            if t.head == token.id and re.match(r'^[A-Z]{1,3}$', t.text):
                if t.deprel in ['parataxis', 'conj', 'nmod']: continue
                return t.text
        return None

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
            if re.match(r'^[A-Z]{2}$', t.text): return t.text
        return None

    def _find_connected_segment(self, point_token: Token, tokens: List[Token]) -> Optional[str]:
        for t in tokens:
            if self._get_entity_type(t.lemma) == "segment":
                seg_label = self._find_label_for_token(t, tokens)
                if seg_label: return seg_label
        return None

    def _check_keyword(self, lemma: str, key_group: str) -> bool:
        return lemma.lower() in self.KEYWORDS.get(key_group, [])

    def _get_entity_type(self, lemma: str) -> Optional[str]:
        for key, values in self.KEYWORDS.items():
            if key.startswith("ENTITY_") and lemma.lower() in values:
                return key.replace("ENTITY_", "").lower()
        return None