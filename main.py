# main.py
import sys
from src.config_loader import load_config
from src.factories import ParserFactory, SaverFactory, GeneratorFactory

def main():
    """
    Orquestra o pipeline completo com base no arquivo config.yaml.
    """
    try:
        config = load_config('config.yaml')
        pipeline_config = config.get('pipeline', {})
        components_config = config.get('components', {})
    except FileNotFoundError:
        print("ERRO: Arquivo 'config.yaml' não encontrado.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERRO ao carregar 'config.yaml': {e}", file=sys.stderr)
        sys.exit(1)

    # Instancia as fábricas
    parser_factory = ParserFactory()
    saver_factory = SaverFactory()
    generator_factory = GeneratorFactory()

    # --- Estágio 1: PARSE ---
    print("\n--- INICIANDO ESTÁGIO 1: PARSE ---")
    try:
        parser_config = components_config.get('parser', {})
        parser = parser_factory.create_parser(parser_config)
        
        input_file = pipeline_config.get('input_log_file')
        lista_de_eventos_fei = parser.parse(input_file)
        print(f"Parseamento concluído. {len(lista_de_eventos_fei)} eventos processados.")
    except Exception as e:
        print(f"ERRO no estágio de Parse: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Estágio 2: SAVE ---
    print("\n--- INICIANDO ESTÁGIO 2: SAVE ---")
    try:
        saver_type = components_config.get('saver', {}).get('type')
        saver = saver_factory.create_saver(saver_type)
        
        intermediate_file = pipeline_config.get('intermediate_fei_file')
        saver.save(lista_de_eventos_fei, intermediate_file)
        print(f"Eventos FEI salvos em '{intermediate_file}'.")
    except Exception as e:
        print(f"ERRO no estágio de Save: {e}", file=sys.stderr)
        sys.exit(1)

    # --- Estágio 3: GENERATE ---
    print("\n--- INICIANDO ESTÁGIO 3: GENERATE ---")
    try:
        generator_type = components_config.get('generator', {}).get('type')
        generator = generator_factory.create_generator(generator_type)
        
        intermediate_file = pipeline_config.get('intermediate_fei_file')
        output_file = pipeline_config.get('output_log_file')
        generator.generate(intermediate_file, output_file)
        print(f"Novo log gerado em '{output_file}'.")
    except Exception as e:
        print(f"ERRO no estágio de Generate: {e}", file=sys.stderr)
        sys.exit(1)
        
    print("\n--- PIPELINE COMPLETO EXECUTADO COM SUCESSO! ---")

if __name__ == "__main__":
    main()