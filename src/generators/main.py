from .factory import GeneratorFactory
from ..config_loader import load_config

def run_generation_stage():
    """
    Orquestra a segunda fase: Caracterização dos eventos FEI
    e criação do modelo estatístico para o executor.
    """
    print("\n Generating model...")

    config = load_config('config.yaml')
    pipeline_config = config.get('pipeline', {})
    generator_config = config.get('components', {}).get('generator', {})

    generator_factory = GeneratorFactory()
    generator = generator_factory.create_generator(generator_config)
    
    input_file = pipeline_config.get('fei_file')
    model_file = pipeline_config.get('output_log_file')

    generator.generate(input_file, model_file)

    print(f"Model generated and saved to '{model_file}'.")

if __name__ == "__main__":
    run_generation_stage()