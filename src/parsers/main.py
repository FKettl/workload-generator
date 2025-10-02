import sys
from .factory import ParserFactory
from ..savers.factory import SaverFactory
from ..config_loader import load_config

def run_parsing_stage():
    """
    Orquestra a primeira fase do pipeline: Análise do log bruto
    e salvamento em um formato intermediário (FEI).
    """
    print("Parsing...")
    try:
        config = load_config('config.yaml')
        pipeline_config = config.get('pipeline', {})
        parser_config = config.get('components', {}).get('parser', {})
        saver_config = config.get('components', {}).get('saver', {})

        parser_factory = ParserFactory()
        saver_factory = SaverFactory()

        parser = parser_factory.create_parser(parser_config)
        saver = saver_factory.create_saver(saver_config)
        
        input_file = pipeline_config.get('input_log_file')
        output_file = pipeline_config.get('fei_file')

        event_iterator = parser.parse(input_file)
        saver.save(list(event_iterator), output_file)

        print(f"Parsing stage completed. Events saved to '{output_file}'.")

    except Exception as e:
        print(f"Error in parsing stage: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    run_parsing_stage()