from typing import Any, Dict
from ..parsers.interfaces import IParser
from .interfaces import IGenerator


class GeneratorFactory:
    """Instantiates the IGenerator implementation based on config."""

    def create_generator(
        self,
        config: Dict[str, Any],
        parser: IParser
    ) -> IGenerator:
        """
        Creates a generator instance, injecting necessary dependencies.

        Args:
            config: The generator's specific configuration dictionary.
            parser: A configured parser instance that will provide domain-specific
                logic (like argument generation) to the generator.
        """
        generator_type = config.get('type')

        if generator_type == 'replay':
            from .replay.replay_generator import ReplayGenerator

            return ReplayGenerator()

        elif generator_type == 'heatmap':
            from .heatmap.heatmap_generator import HeatmapGenerator

            interval = config.get('percentage_interval', 5)
            simulation_duration_s = config.get('simulation_duration_s', 30)

            return HeatmapGenerator(
                parser=parser,
                percentage_interval=interval,
                simulation_duration_s=simulation_duration_s
            )
        else:
            raise ValueError(f"Generator type '{generator_type}' is not supported.")