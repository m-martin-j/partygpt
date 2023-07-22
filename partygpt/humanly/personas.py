
import random
import logging


logger = logging.getLogger(__name__)


class Persona:
    def __init__(
            self,
            sampling_space: dict=None,
            character: str=None,
            profession: str=None,
            experience: str=None,
            aspiration: str=None,
            special_skill: str=None) -> None:

        if sampling_space is None:  # set traits specifically
            if None in [character, profession, experience, aspiration, special_skill]:
                raise ValueError('If sampling_space is None, other Persona arguments must be provided')
            self.character = character
            self.profession = profession
            self.experience = experience
            self.aspiration = aspiration
            self.special_skill = special_skill

        elif isinstance(sampling_space, dict):  # set traits randomly
            self._sampling_space = sampling_space
            self.sample_randomly()
        else:
            raise ValueError('Unexpected type of sampling_space.')

    def sample_randomly(self) -> None:
        for key, value_list in self._sampling_space.items():
            selection = random.choice(value_list)
            if key == 'character':
                self.character = selection
            elif key == 'profession':
                self.profession = selection
            elif key == 'experience':
                self.experience = selection
            elif key == 'aspiration':
                self.aspiration = selection
            elif key == 'special_skill':
                self.special_skill = selection
            else:
                raise ValueError(f'Unexpected element "{key}" in sampling_space.')

    def characterize(self) -> str:
        res = \
            self.character + ' ' + \
            self.profession + ' ' + \
            self.experience + ' ' + \
            self.aspiration + ' ' + \
            self.special_skill
        logger.info(f'Persona characterized: {res}')
        return res

    @property
    def character(self) -> str:
        return self._character

    @character.setter
    def character(self, value) -> None:
        self._character = f'You are a {value} person.'


    @property
    def profession(self) -> str:
        return self._profession

    @profession.setter
    def profession(self, value) -> None:
        self._profession = f'You are a {value}.'  # TODO


    @property
    def experience(self) -> str:
        return self._experience

    @experience.setter
    def experience(self, value) -> None:
        self._experience = f'You have {value} today.'


    @property
    def aspiration(self) -> str:
        return self._aspiration

    @aspiration.setter
    def aspiration(self, value) -> None:
        self._aspiration = f'Tell our guest that {value}.'

    @property
    def special_skill(self) -> str:
        return self._special_skill

    @special_skill.setter
    def special_skill(self, value) -> None:
        self._special_skill = f'You can {value}.'
