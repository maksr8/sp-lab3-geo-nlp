import json
from src.nlp_engine import UDPipeClient
from src.preprocessor import TextPreprocessor
from src.extractor import GeometryExtractor
from src.geometry import GeometryPlotter


def print_udpipe_table(tokens):
    print(f"   {'ID':<4} {'TEXT':<15} {'LEMMA':<15} {'UPOS':<6} {'HEAD':<6} {'DEPREL':<10}")
    print("   " + "-" * 60)
    for t in tokens:
        print(f"   {t.id:<4} {t.text:<15} {t.lemma:<15} {t.upos:<6} {t.head:<6} {t.deprel:<10}")
    print("   " + "-" * 60)


def main():
    DEBUG_SHOW_UDPIPE = True
    DEBUG_SHOW_FULL_JSON = True

    client = UDPipeClient()
    preprocessor = TextPreprocessor()
    extractor = GeometryExtractor()
    plotter = GeometryPlotter()

    raw_task_text = "169.• На стороні BC трикутника ABC позначили точку M. Периметри трикутників ABC, AMC і AMB дорівнюють відповідно 60 см, 36 см і 50 см. Знайдіть відрізок AM."

    print(f"\n>>> Raw Input: {raw_task_text}")

    full_clean_text = preprocessor.clean(raw_task_text)
    print(f">>> Cleaned Text: {full_clean_text}")

    sentences = list(filter(None, full_clean_text.split('.')))
    all_commands = []

    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence: continue

        print(f"\n   [Sentence {i + 1}]: '{sentence}'")

        tokens = client.analyze(sentence)

        if DEBUG_SHOW_UDPIPE:
            print_udpipe_table(tokens)

        commands_list = extractor.extract_structure(tokens)

        if commands_list:
            for cmd in commands_list:
                if cmd.get("command") != "UNKNOWN":
                    print(f"     [FOUND]: {cmd['entity'].upper()} ({cmd['command']}) -> Label: {cmd.get('label')}")

                    if DEBUG_SHOW_FULL_JSON:
                        print(f"     [JSON]: {json.dumps(cmd, ensure_ascii=False)}")

                    all_commands.append(cmd)
        else:
            print("     [INFO] No geometry commands found.")

    print(f"\n>>> Total commands to draw: {len(all_commands)}")

    if all_commands:
        try:
            plotter.execute_commands(all_commands)
            plotter.plot()
            print(">>> Drawing successful.")
        except Exception as e:
            print(f">>> Drawing Error: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(">>> Nothing to draw.")


if __name__ == "__main__":
    main()