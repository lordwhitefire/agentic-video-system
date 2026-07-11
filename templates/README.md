# Templates

This folder contains video editing style templates extracted from reference videos.

Each template is a JSON file that captures the STRUCTURAL TEMPLATE of a reference video — not its content. The template can be applied to any topic.

## Template Structure

```json
{
  "template_name": "commentary-long-form",
  "reference_source": "description of reference video",
  "form": "long",
  "genre": "commentary",
  "duration_target": "12-15 minutes",
  "structure": [
    {
      "segment_id": "cold_open",
      "label": "Cold Open",
      "duration_percentage": 1-3%,
      "purpose": "Pattern interrupt. Establish the paradox.",
      "visual_style": "Split screen or rapid cut between contrasting footage"
    },
    {
      "segment_id": "hook",
      "label": "Hook",
      "duration_percentage": 5-8%,
      "purpose": "Establish the pattern. Tease the breakdown.",
      "visual_style": "B-roll of evidence, fast cutting, transition to WHY graphic"
    }
  ],
  "cut_rhythm": {
    "avg_shot_length": "2-4 seconds",
    "pacing_curve": "Fast at open and conclusion, slower during extended analysis"
  },
  "visual_vocabulary": {
    "b_roll_types": ["match footage", "pundit clips", "archive"],
    "graphic_templates": ["dark grid + particles", "gradient + image + text"],
    "color_grade": "Varies by source — warm for B-roll, dark for stats"
  },
  "audio_structure": {
    "layers": 2,
    "description": "Voice commentary + background music bed (ducked to 10%)",
    "authority_clips": "Every 30-40 seconds, 10-15s authority clip with own audio"
  },
  "transitions": {
    "type": "Crossfade at narrative breakpoints",
    "frequency": "5-8 per video, at story shifts only"
  }
}
```

## How to Use

1. Analyzer perceives a reference video → extracts template
2. Template is saved in this folder
3. Planner loads template + applies it to user's topic
4. Editor follows template structure for assembly

## Adding New Templates

When you analyze a new reference video, save the template here with a descriptive name:
- `commentary-long-form.json`
- `reaction-short-form.json`
- `essay-medium-form.json`
- etc.
