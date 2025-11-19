import requests
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Token:
    """
    Represents a single word (token) in the dependency tree.
    """
    id: int
    text: str
    lemma: str
    upos: str  # Universal Part of Speech
    head: int  # ID of the parent word
    deprel: str  # Dependency relation
    feats: str


class UDPipeClient:
    """
    Client for interacting with the UDPipe API.
    """
    MODEL = "ukrainian-iu-ud-2.15-241121"
    API_URL = "http://lindat.mff.cuni.cz/services/udpipe/api/process"

    def analyze(self, text: str) -> List[Token]:
        """
        Sends text to UDPipe and returns a list of Token objects.

        :param text: Raw input text (e.g., "Побудувати висоту.")
        :return: List of Token objects representing the parsed sentence.
        """
        params = {
            "tokenizer": "",
            "tagger": "",
            "parser": "",
            "model": self.MODEL,
            "data": text
        }

        try:
            response = requests.get(self.API_URL, params=params)
            response.raise_for_status()
            result_text = response.json().get('result', '')
            return self._parse_conllu(result_text)
        except requests.exceptions.RequestException as e:
            print(f"Error connecting to UDPipe: {e}")
            return []

    def _parse_conllu(self, conllu_text: str) -> List[Token]:
        """
        Parses raw CoNLL-U string format into Python objects.
        """
        tokens = []
        lines = conllu_text.strip().split('\n')

        for line in lines:
            if line.startswith('#') or not line.strip():
                continue

            parts = line.split('\t')

            if len(parts) < 10:
                continue

            if '-' in parts[0]:
                continue

            try:
                token = Token(
                    id=int(parts[0]),
                    text=parts[1],
                    lemma=parts[2],
                    upos=parts[3],
                    head=int(parts[6]),
                    deprel=parts[7],
                    feats=parts[5]
                )
                tokens.append(token)
            except ValueError:
                continue

        return tokens


if __name__ == "__main__":
    client = UDPipeClient()
    sample_text = "Побудувати висоту до гіпотенузи."
    tokens = client.analyze(sample_text)

    print(f"{'ID':<4} {'TEXT':<15} {'LEMMA':<15} {'UPOS':<6} {'HEAD':<6} {'DEPREL':<10}")
    print("-" * 60)
    for t in tokens:
        print(f"{t.id:<4} {t.text:<15} {t.lemma:<15} {t.upos:<6} {t.head:<6} {t.deprel:<10}")