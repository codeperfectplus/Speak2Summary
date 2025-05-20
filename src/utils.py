from markdown import markdown
from bs4 import BeautifulSoup, Tag
import re

TAG_STYLES = {
    'h1': 'text-4xl font-extrabold text-indigo-800 mb-6 mt-8 scroll-mt-24 flex justify-between items-center',
    'h2': 'text-3xl font-bold text-indigo-700 mb-5 mt-7 scroll-mt-24 flex justify-between items-center',
    'h3': 'text-2xl font-semibold text-indigo-600 mb-4 mt-6 flex justify-between items-center',
    'h4': 'text-xl font-medium text-indigo-500 mb-3 mt-5',
    'h5': 'text-lg font-medium text-indigo-400 mb-2 mt-4',
    'h6': 'text-base font-medium text-indigo-300 mb-1 mt-3',
    'p': 'mb-4 text-gray-800 leading-relaxed tracking-normal',
    'ul': 'list-disc list-inside pl-6 mb-4 text-gray-800',
    'ol': 'list-decimal list-inside pl-6 mb-4 text-gray-800',
    'li': 'mb-1',
    'blockquote': 'border-l-4 border-blue-400 pl-6 italic text-gray-700 bg-blue-50 py-3 px-4 rounded-md my-6',
    'hr': 'my-8 border-t border-gray-300',
    'a': 'text-blue-700 hover:text-blue-900 underline',
    'code': 'bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-purple-700',
    'pre': 'bg-gray-100 text-gray-800 p-5 rounded-lg overflow-x-auto text-sm shadow-inner my-6 whitespace-pre-wrap break-words',
    'table': 'table-auto w-full border-collapse border border-gray-300 shadow-sm my-8 text-sm',
    'thead': 'bg-gray-100',
    'th': 'border px-4 py-3 text-left bg-gray-200 text-gray-700 font-semibold',
    'td': 'border px-4 py-2 text-gray-800'
}

HEADING_TAGS = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']

def wrap_collapsible(start_tag, soup):
    """
    Wraps content under heading inside a collapsible div with toggle icon
    """
    level = int(start_tag.name[1])
    toggle_id = f"section-{id(start_tag)}"
    content_div = soup.new_tag("div", **{'id': toggle_id, 'class': 'collapsible-content'})

    next_sibling = start_tag.find_next_sibling()
    while next_sibling and (
        not isinstance(next_sibling, Tag)
        or next_sibling.name not in HEADING_TAGS
        or int(next_sibling.name[1]) > level
    ):
        temp = next_sibling
        next_sibling = next_sibling.find_next_sibling()
        content_div.append(temp.extract())

    start_tag.insert_after(content_div)

    # Add toggle button
    toggle_button = soup.new_tag("button", **{
        'class': 'toggle-button text-indigo-700 text-xl font-bold ml-2 focus:outline-none',
        'onclick': f"toggleContent('{toggle_id}', this)"
    })
    toggle_button.string = '+'
    start_tag.append(toggle_button)

def fix_nested_lists(soup):
    for ul in soup.find_all(['ul', 'ol']):
        for li in ul.find_all('li', recursive=False):
            next_elem = li.find_next_sibling()
            if next_elem and next_elem.name in ['ul', 'ol']:
                nested_list = next_elem.extract()
                li.append(nested_list)

def process_nested_items(soup):
    for li in soup.find_all('li'):
        if li.strong and li.strong.text.strip().endswith(':'):
            next_sibling = li.find_next_sibling()
            sublist = soup.new_tag('ul', **{'class': TAG_STYLES['ul'].split()})
            while next_sibling and next_sibling.name == 'li' and not next_sibling.strong:
                temp = next_sibling
                next_sibling = next_sibling.find_next_sibling()
                sublist.append(temp.extract())
            if sublist.find('li'):
                li.append(sublist)

def handle_special_formatting(soup):
    for code in soup.find_all('code'):
        if code.parent.name != 'pre':
            code['class'] = TAG_STYLES['code'].split()
    # Leave checkbox syntax unchanged

def render_minutes_with_tailwind(md_text: str) -> str:
    html = markdown(md_text, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br', 'extra'])
    soup = BeautifulSoup(html, 'html.parser')

    fix_nested_lists(soup)
    process_nested_items(soup)
    handle_special_formatting(soup)

    for tag in soup.find_all(HEADING_TAGS):
        level = int(tag.name[1])
        if level <= 3:
            wrap_collapsible(tag, soup)

    for tag_name, class_list in TAG_STYLES.items():
        for el in soup.find_all(tag_name):
            if tag_name == 'code' and el.parent.name == 'pre':
                continue
            existing_classes = el.get('class', [])
            el['class'] = list(set(existing_classes + class_list.split()))
            if tag_name == 'a':
                el['target'] = '_blank'
                el['rel'] = 'noopener noreferrer'

    return str(soup)

if __name__ == "__main__":
    with open("data.md", "r") as f:
        md_text = f.read()

    html = render_minutes_with_tailwind(md_text)
    with open("output.html", "w") as f:
        f.write(html)
