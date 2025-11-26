import os
import yaml
import xml.etree.ElementTree as ET
from pathlib import Path
from crewai import Agent, Task, Crew, Process
from crewai_tools import XMLSearchTool

# === CONFIGURATION ===
XML_FILE = "data/export.xml"
STRUCTURE_FILE = "config/structure.yaml"
TEMPLATES_DIR = "templates"
OUTPUT_DIR = "output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load structure.yaml
with open(STRUCTURE_FILE, "r") as f:
    structure = yaml.safe_load(f)

# Initialize the XML Tool
xml_tool = XMLSearchTool(file_path=XML_FILE)

# Define Agents (used symbolically for tasks here)
extractor = Agent(
    role="XML Extractor",
    goal="Extract relevant content blocks from the XML export",
    backstory="You specialize in mining structured knowledge from XML data exports.",
    tools=[xml_tool],
    verbose=True,
    memory=True,
)

builder = Agent(
    role="Content Rebuilder",
    goal="Rebuild pages using the correct template and extracted content",
    backstory="You are a formatting wizard who turns raw data into beautiful, readable pages.",
    verbose=True,
    memory=True,
)

# === HELPERS FOR XML PARSING AND OUTPUT ===

def parse_xml_string(xml_str: str):
    try:
        return ET.fromstring(xml_str)
    except ET.ParseError as e:
        print(f"⚠️ XML Parse Error: {e}")
        return None

def get_text_from_path(elem, path: str):
    target = elem
    for part in path.split("/"):
        if target is not None:
            target = target.find(part)
        else:
            break
    return target.text.strip() if target is not None and target.text else f"[{path} not found]"

def get_nth_section_text(root, n: int):
    sections = root.findall("section")
    if len(sections) >= n:
        return sections[n - 1].text.strip() if sections[n - 1].text else ""
    return f"[section {n} not found]"

def extract_content(xml_tool, page_id):
    raw_xml = xml_tool.search(f'id="{page_id}"')
    if not raw_xml:
        print(f"⚠️ No XML content found for page_id={page_id}")
        return {}

    root = parse_xml_string(raw_xml)
    if root is None:
        return {}

    return {
        "page_title": page_id.split("/")[-1].replace("-", " ").title(),

        # General content
        "introduction": get_text_from_path(root, "introduction"),
        "conclusion": get_text_from_path(root, "conclusion"),

        # Sections
        "section_1_heading": "Overview",
        "section_1_content": get_nth_section_text(root, 1),
        "section_2_heading": "Details",
        "section_2_content": get_nth_section_text(root, 2),

        # FAQ (example)
        "faq_1_question": get_text_from_path(root, "faq/q"),
        "faq_1_answer": get_text_from_path(root, "faq/a"),
        "faq_2_question": "Where does this content come from?",
        "faq_2_answer": "This content was extracted from the original XML knowledge base.",

        # Tutorial steps
        "step_1_title": "Step One",
        "step_1_content": get_text_from_path(root, "steps/step1"),
        "step_2_title": "Step Two",
        "step_2_content": get_text_from_path(root, "steps/step2"),
    }

def load_template(template_name):
    template_path = Path(TEMPLATES_DIR) / f"{template_name}.yaml"
    if not template_path.exists():
        print(f"⚠️ Template '{template_name}' not found.")
        return None
    with open(template_path, "r") as f:
        return yaml.safe_load(f)["page_template"]

def fill_template(template: dict, data: dict):
    def recursive_replace(obj):
        if isinstance(obj, str):
            return obj.format(**data)
        elif isinstance(obj, list):
            return [recursive_replace(i) for i in obj]
        elif isinstance(obj, dict):
            return {k: recursive_replace(v) for k, v in obj.items()}
        else:
            return obj
    return recursive_replace(template)

def save_markdown(output_path, content):
    with open(output_path, "w") as f:
        if isinstance(content, dict):
            for key, val in content.items():
                if isinstance(val, list):
                    for item in val:
                        f.write(f"\n### {item.get('heading', item.get('title', ''))}\n")
                        f.write(item.get('body', item.get('content', '')) + "\n")
                else:
                    f.write(f"{val}\n\n")
        else:
            f.write(content)

def dict_to_xml(tag, data):
    elem = ET.Element(tag)
    for key, val in data.items():
        if isinstance(val, list):
            for item in val:
                child = ET.SubElement(elem, key)
                for sub_key, sub_val in item.items():
                    sub_elem = ET.SubElement(child, sub_key)
                    sub_elem.text = str(sub_val)
        elif isinstance(val, dict):
            child = ET.SubElement(elem, key)
            for sub_key, sub_val in val.items():
                sub_elem = ET.SubElement(child, sub_key)
                sub_elem.text = str(sub_val)
        else:
            child = ET.SubElement(elem, key)
            child.text = str(val)
    return elem

# === MAIN PROCESSING FUNCTION ===

def process_pages(pages, default_template):
    page_xml_elements = []

    for page in pages:
        page_id = page["id"]
        title = page["title"]
        template_name = page.get("template", default_template)
        print(f"\n📄 Building page: {title} ({page_id}) using template: {template_name}")

        template = load_template(template_name)
        if not template:
            continue

        content_data = extract_content(xml_tool, page_id)
        filled = fill_template(template, content_data)

        # Save Markdown
        output_path = Path(OUTPUT_DIR) / f"{page_id}.md"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        save_markdown(output_path, filled)
        print(f"✅ Created Markdown: {output_path}")

        # Create <page> XML element
        page_elem = dict_to_xml("page", filled)
        page_elem.set("id", page_id)
        page_xml_elements.append(page_elem)

    return page_xml_elements

# === BUILD EVERYTHING ===

all_pages = []

for category in structure["knowledge_base"]:
    default_template = category.get("template", "default_page")

    if "pages" in category:
        all_pages += process_pages(category["pages"], default_template)

    for sub in category.get("subcategories", []):
        sub_template = sub.get("template", default_template)
        all_pages += process_pages(sub.get("pages", []), sub_template)

# Combine all pages into a single <knowledge_base> XML
root = ET.Element("knowledge_base")
for page_elem in all_pages:
    root.append(page_elem)

tree = ET.ElementTree(root)
xml_output_path = Path(OUTPUT_DIR) / "knowledge_base.xml"
tree.write(xml_output_path, encoding="utf-8", xml_declaration=True)
print(f"\n📦 Final combined XML saved to: {xml_output_path}")
