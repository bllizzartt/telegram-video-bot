"""
Prompt templates for video generation.
Provides curated prompts for different video styles.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class PromptTemplate:
    """A prompt template for video generation."""

    name: str
    description: str
    prompt: str
    category: str


# Predefined templates
TEMPLATES = [
    # Lifestyle & Travel
    PromptTemplate(
        name="Dancing in Tokyo",
        description="Dynamic dance movement in a futuristic city",
        prompt="A person dancing energetically in the streets of Tokyo at night, neon lights reflecting off wet pavement, cherry blossoms floating in the air, cinematic lighting, steady cam movement",
        category="lifestyle",
    ),
    PromptTemplate(
        name="Walking Through Paris",
        description="Romantic walk through Parisian streets",
        prompt="A person walking leisurely through the streets of Paris, old stone buildings with wrought iron balconies, golden hour light streaming through clouds, café terraces visible in background, dreamy atmosphere",
        category="lifestyle",
    ),
    PromptTemplate(
        name="Yoga by the Ocean",
        description="Peaceful yoga session at sunrise",
        prompt="A person practicing yoga on a beach at sunrise, golden light over calm ocean waves, gentle breeze moving their hair, peaceful and meditative mood, wide establishing shot",
        category="lifestyle",
    ),
    # Professional
    PromptTemplate(
        name="Presenting at Conference",
        description="Professional presentation in a conference hall",
        prompt="A person confidently presenting at a modern conference hall, audience visible in background, large screen displaying charts, professional lighting, dynamic hand gestures",
        category="professional",
    ),
    PromptTemplate(
        name="Tech Startup Pitch",
        description="Pitching to investors",
        prompt="A person sitting across from investors at a sleek conference table, startup office environment, whiteboard with diagrams visible, natural conversation, startup casual attire",
        category="professional",
    ),
    PromptTemplate(
        name="Teaching a Class",
        description="Engaging classroom environment",
        prompt="A person teaching in a modern classroom, students engaged in background, smart board with educational content, warm and interactive atmosphere, natural lighting",
        category="professional",
    ),
    # Creative & Fantasy
    PromptTemplate(
        name="Cyberpunk City",
        description="Futuristic cyberpunk aesthetic",
        prompt="A person standing in a futuristic cyberpunk city, neon signs in multiple languages, flying vehicles in background, rain-slicked streets with reflections, dramatic volumetric lighting",
        category="creative",
    ),
    PromptTemplate(
        name="Fantasy Forest",
        description="Enchanted forest scene",
        prompt="A person walking through an enchanted forest, magical glowing creatures visible between trees, rays of sunlight breaking through canopy, fairy tale atmosphere, ethereal lighting",
        category="creative",
    ),
    PromptTemplate(
        name="Space Station",
        description="Sci-fi space environment",
        prompt="A person floating inside a space station, Earth visible through large window, zero gravity environment, sleek metallic corridors, cosmic background visible, documentary style",
        category="creative",
    ),
    # Fashion & Style
    PromptTemplate(
        name="Fashion Shoot",
        description="Professional fashion photography style",
        prompt="A person posing for a fashion photoshoot in an urban location, multiple outfit changes, professional camera equipment visible, magazine-quality lighting and composition",
        category="fashion",
    ),
    PromptTemplate(
        name="Street Style",
        description="Casual urban fashion",
        prompt="A person walking confidently down a trendy urban street, street art background, natural candid photography style, vibrant city atmosphere",
        category="fashion",
    ),
    # Sports & Action
    PromptTemplate(
        name="Mountain Hiking",
        description="Adventure sports activity",
        prompt="A person hiking through mountain terrain, dramatic alpine scenery, snow-capped peaks in background, adventurous spirit, dynamic action shot",
        category="sports",
    ),
    PromptTemplate(
        name="Surfing at Sunset",
        description="Beach sports action",
        prompt="A person surfing expert-level waves at golden hour, orange and pink sunset sky, tropical beach setting, dynamic action cinematography, spray of water",
        category="sports",
    ),
]


def get_templates_by_category(category: str) -> List[PromptTemplate]:
    """Get templates filtered by category."""
    return [t for t in TEMPLATES if t.category == category]


def get_all_categories() -> List[str]:
    """Get all available categories."""
    return sorted(set(t.category for t in TEMPLATES))


def get_template_by_name(name: str) -> PromptTemplate:
    """Get a specific template by name."""
    for template in TEMPLATES:
        if template.name.lower() == name.lower():
            return template
    raise ValueError(f"Template not found: {name}")


def format_templates_list() -> str:
    """Format all templates as a readable list."""
    categories = get_all_categories()
    lines = ["🎬 *Available Prompt Templates*\n"]

    for category in categories:
        lines.append(f"\n📂 *{category.title()}*\n")
        for template in get_templates_by_category(category):
            lines.append(f"• *{template.name}*")
            lines.append(f"  _{template.description}_")

    return "\n".join(lines)


def format_quick_templates() -> str:
    """Format templates as quick buttons for Telegram."""
    # Return first 6 templates for quick selection
    quick = TEMPLATES[:6]
    lines = ["*Quick Templates:*\n"]
    for i, template in enumerate(quick, 1):
        lines.append(f"{i}. {template.name}")
    return "\n".join(lines)
