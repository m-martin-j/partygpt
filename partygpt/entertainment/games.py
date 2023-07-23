
# TODO: functionality not yet integrated

class Game:
    def __init__(
            self,
            settings) -> None:
        self._game_settings = settings['games']


class Joke(Game):
    def __init__(self) -> None:
        super().__init__()
        self._joke_settings = self._game_settings['jokes']
        self.request_input = self._joke_settings['request_prompt']

    def request_joke(self, request_input):
        return request_input
