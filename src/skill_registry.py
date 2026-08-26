from src.skill import Skill


class SkillRegistry:
    def __init__(
        self,
    ) -> None:
        self._skills: dict[str, Skill] = {}

    def register(
        self,
        skill: Skill,
    ) -> None:
        self._skills[skill.name] = skill

    def get(
        self,
        name: str,
    ) -> Skill:
        try:
            return self._skills[name]
        except KeyError:
            raise ValueError(
                f"Unknown skill: {name}"
            )

    def list_skills(
        self,
    ) -> list[Skill]:
        return list(
            self._skills.values()
        )

    def descriptions(
        self,
    ) -> list[dict[str, str]]:
        return [
            {
                "name": skill.name,
                "description": skill.description,
            }
            for skill in self._skills.values()
        ]