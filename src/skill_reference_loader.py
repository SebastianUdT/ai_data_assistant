from dataclasses import dataclass

from src.skill import Skill


@dataclass
class SkillReference:
    skill_name: str
    reference_name: str
    content: str


class SkillReferenceLoader:
    def load(
        self,
        skill: Skill,
        reference_name: str,
    ) -> SkillReference:
        content = skill.get_reference(
            reference_name
        )

        return SkillReference(
            skill_name=skill.name,
            reference_name=reference_name,
            content=content,
        )