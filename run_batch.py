import pandas as pd
import os
from src.nlp_engine import UDPipeClient
from src.preprocessor import TextPreprocessor
from src.extractor import GeometryExtractor
from src.geometry import GeometryPlotter


def process_batch():
    input_file = os.path.join("data", "taskbank.xlsx")
    output_dir = "output"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    if not os.path.exists(input_file):
        print(f"ERROR: File not found: {input_file}")
        return

    try:
        df = pd.read_excel(input_file)
    except Exception as e:
        print(f"Pandas Error: {e}")
        return

    client = UDPipeClient()
    preprocessor = TextPreprocessor()
    extractor = GeometryExtractor()

    print(f">>> Processing {len(df)} tasks from {input_file}")

    for index, row in df.iterrows():
        try:
            task_id = row.iloc[0]
            text = str(row.iloc[1])
        except:
            continue

        print(f"\nTask #{task_id}: {text[:50]}...")

        clean_text = preprocessor.clean(text)
        sentences = list(filter(None, clean_text.split('.')))

        all_commands = []

        for sentence in sentences:
            tokens = client.analyze(sentence)
            cmds = extractor.extract_structure(tokens)
            if cmds:
                all_commands.extend(cmds)

        if all_commands:
            plotter = GeometryPlotter()
            try:
                plotter.execute_commands(all_commands)
                save_path = os.path.join(output_dir, f"task_{task_id}.png")
                plotter.plot(save_path=save_path)
            except Exception as e:
                print(f"   [ERROR Drawing] {e}")
        else:
            print("   [SKIPPED] No geometry found.")


if __name__ == "__main__":
    process_batch()