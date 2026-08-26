from src.skill import Skill
from src.skill_registry import SkillRegistry


class SkillSelector:
    def __init__(
        self,
        registry: SkillRegistry,
    ) -> None:
        self.registry = registry

    def select(
        self,
        user_message: str,
    ) -> Skill | None:
        message = user_message.lower()

        for skill in self.registry.list_skills():
            searchable_text = (
                skill.name.replace("_", " ")
                + " "
                + skill.description
            ).lower()

            words = searchable_text.split()

            for word in words:
                if (
                    len(word) >= 4
                    and word in message
                ):
                    return skill

        return None