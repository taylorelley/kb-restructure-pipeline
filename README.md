# Knowledge Base Restructuring with CrewAI

This project automates the extraction, restructuring, and formatting of a knowledge base exported in XML format. It uses CrewAI to manage a set of agents that parse the XML, apply templates, rebuild the structure, and output both Markdown and XML.

## Project Structure

```
.
├── config/
│   └── structure.yaml          # Defines hierarchy and template mapping
├── templates/
│   ├── default_page.yaml       # Generic page template
│   ├── faq_page.yaml           # FAQ page template
│   └── tutorial_page.yaml      # Tutorial template
├── data/
│   └── export.xml              # Original XML export
├── output/
│   ├── {page_id}.md            # Generated Markdown pages
│   └── knowledge_base.xml      # Combined XML output
├── src/
│   └── crew.py                 # Main processor
└── README.md
```

## How It Works

1. `crew.py` reads `config/structure.yaml`.
2. Each page loads its assigned template.
3. Content is extracted from `data/export.xml` with XMLSearchTool.
4. Output includes:
   - A Markdown file for each page.
   - A combined XML file containing all processed pages.

## structure.yaml Example

```yaml
knowledge_base:
  - category: "Getting Started"
    template: "default_page"
    pages:
      - title: "Welcome"
        id: "getting_started/welcome"
        template: "default_page"

      - title: "Installation"
        id: "getting_started/installation"
        template: "tutorial_page"

  - category: "Support"
    pages:
      - title: "FAQs"
        id: "support/faqs"
        template: "faq_page"
```

## Running the Project

### Requirements

- Python 3.10+
- CrewAI
- crewai-tools (XMLSearchTool)
- Environment variables:
  - `OPENAI_API_KEY`
  - `SERPER_API_KEY` (optional)

### Install Dependencies

```
pip install -r requirements.txt
```

### Run the Processor

```
cd src
python crew.py
```

This creates:

- `output/{page_id}.md`  
- `output/knowledge_base.xml`

## Customization

### Add Templates

Add more YAML templates under `/templates` and reference them in `structure.yaml`.

### Extend XML Support

For advanced handling such as block references, update `extract_content()` in `crew.py`.

## Example Output

```
output/
├── getting_started/
│   ├── welcome.md
│   └── installation.md
├── support/
│   └── faqs.md
└── knowledge_base.xml
```

## To‑Do

- Add XSD schema validation
- CLI to build selected sections
- Human review step
- Shared block reuse handling

## Tools Used

- CrewAI
- crewai_tools.XMLSearchTool
- OpenAI GPT agents
